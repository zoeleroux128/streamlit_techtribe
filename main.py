import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import asyncio
import websockets
import json
import time
import base64

# NOTE: Assume data looks something like:
# {"temperature_c": 54, "cpu_usage_percent": 51, "timestamp": 1737612795.0035408}

def stop():
    st.session_state.is_connected = False
    if 'websocket_task' in st.session_state and st.session_state.websocket_task:
        st.session_state.websocket_task.cancel() # Attempt to cancel the running task
        st.session_state.websocket_task = None

def start():
    st.session_state.is_connected = True

# Streamlit Dashboard
st.title("WebSocket Live Data Viewer")

# Setting up this way allows us to return to login screen after Stop button
if "is_connected" not in st.session_state:
    st.session_state["is_connected"] = False

if "all_data" not in st.session_state:
    st.session_state["all_data"] = pd.DataFrame()

if "last_redraw" not in st.session_state:
    st.session_state["last_redraw"] = 0

# Authentication and options
if not st.session_state.is_connected:
    st.text_input("Websocket base URL", type="default", key="wss_root_url", value="ws://localhost:80")
    st.text_input("Websocket Username", type="default", key="wss_username", value="")
    st.text_input("Websocket Password", type="password", key="wss_password", value="")
    st.text_input("Stream Keys", type="default", key="stream_key", value="*")
    st.text_input("Columns", type="default", key="columns", value="*")
    st.text_input("Max data points", type="default", key="max_points", value=10000)
    st.button("Start!", on_click=start)
else:
    st.button("Stop", on_click=stop)

    # Placeholders for dynamic updates
    status_placeholder = st.empty()
    plot_placeholder = st.empty()

    async def run_websocket_client():
        columns = "*" if st.session_state.columns == "*" else st.session_state.columns.split(",")
        max_points = int(st.session_state.max_points)

        auth_token = base64.b64encode(f"{st.session_state.wss_username}:{st.session_state.wss_password}".encode()).decode()
        headers = [("Authorization", f"Basic {auth_token}")]
        url = f"{st.session_state.wss_root_url}/{st.session_state.stream_key}"

        status_placeholder.write(f"Connecting to WebSocket {url}...")

        try:
            async with websockets.connect(url, additional_headers=headers) as ws:
                status_placeholder.write("Connected! Waiting for data...")
                while st.session_state.is_connected:
                    try:
                        # Set a timeout for receiving data to allow checking st.session_state.is_connected
                        data_raw = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(data_raw)

                        timestamp = data.pop("timestamp")
                        data = data if columns == "*" else {k: data[k] for k in columns}
                        record = pd.DataFrame(data, index=[pd.to_datetime(timestamp, unit="ms")])

                        # Append new record, remove oldest records if max is reached
                        if st.session_state.all_data.empty:
                            st.session_state.all_data = record
                        else:
                            st.session_state.all_data = pd.concat([st.session_state.all_data, record]).sort_index().iloc[-max_points:]

                        # Redraw plot no sooner than 250ms since last drawn
                        current_time = time.time()
                        if current_time - st.session_state.last_redraw >= 0.25:
                            fig = go.Figure()
                            fig.update_layout(
                                title=f"Latest {max_points} Events Stream",
                                xaxis_title="Timestamp",
                                yaxis_title="Column Values",
                                legend_title="Column Names",
                            )
                            fig.add_traces([
                                go.Scatter(
                                    x=st.session_state.all_data.index,
                                    y=st.session_state.all_data[column],
                                    mode='lines',
                                    name=column
                                ) for column in st.session_state.all_data.columns
                            ])

                            plot_placeholder.plotly_chart(
                                fig,
                                use_container_width=True,
                                key=current_time # Use current_time as key to force re-render
                            )
                            st.session_state.last_redraw = current_time

                    except asyncio.TimeoutError:
                        # No data received within the timeout, check is_connected again
                        pass
                    except websockets.exceptions.ConnectionClosedOK:
                        status_placeholder.error("WebSocket connection closed gracefully.")
                        st.session_state.is_connected = False
                        break
                    except Exception as e:
                        status_placeholder.error(f"WebSocket error: {e}")
                        st.session_state.is_connected = False
                        break

        except websockets.exceptions.ConnectionRefused:
            status_placeholder.error("Connection refused. Check URL and server status.")
            st.session_state.is_connected = False
        except Exception as e:
            status_placeholder.error(f"Failed to connect: {e}")
            st.session_state.is_connected = False

        status_placeholder.write("WebSocket connection ended.")
        print("Websocket connection ended.")

    # How to run the async function in Streamlit without blocking:
    # This is still a bit tricky as Streamlit re-runs the entire script.
    # The common workaround is to use a separate thread or a library like `streamlit-autorefresh`
    # or `streamlit-websocket-component` for true background processing.
    #
    # For this specific case, the simplest way to allow Streamlit to render while
    # attempting to run the async client is to use `asyncio.run` but acknowledge
    # that it will block the Streamlit thread until the connection is closed or
    # the 'Stop' button is clicked.

    # To make it truly non-blocking and allow the 'Stop' button to work effectively
    # by letting Streamlit re-render, you'd ideally run this in a separate thread.
    # However, since direct threading/async in Streamlit's main loop is challenging
    # for long-running tasks, let's go with a more Streamlit-idiomatic approach
    # if you want live updates without manual refresh.

    # Option 1: Using `streamlit-autorefresh` (recommended for periodic updates)
    # This isn't a direct WebSocket continuous stream but can fetch data periodically.
    # You would typically use this if your websocket server provides a REST endpoint
    # to pull data, or if you establish and close the websocket connection frequently.

    # Option 2: Running in a background thread (more robust for continuous streaming)
    # This requires more boilerplate for thread management and data sharing.

    # For now, let's make `asyncio.run` conditional and manage the task lifecycle.
    # The core issue remains that `asyncio.run()` blocks the Streamlit thread.

    # A better approach for this kind of persistent connection in Streamlit is to
    # use a library designed for long-running background tasks, or run your
    # WebSocket client as a separate service and have Streamlit poll it or
    # receive updates via another mechanism (e.g., a message queue).

    # For the immediate problem of *not opening in a browser*, the most likely cause
    # is that the script is blocking on `asyncio.run(websocket_handler())`
    # immediately upon starting due to `st.session_state.is_connected` potentially being True
    # from a previous run or not being initialized as False.

    # Let's ensure the asyncio task is managed properly for Streamlit's re-run cycle.
    # The `asyncio.run` call is the problem. Streamlit's main loop is not an event loop.
    # You cannot call `asyncio.run` directly in the Streamlit script's main execution flow
    # for a long-running task.

    # The most common workaround for Streamlit to handle *some* async operations
    # without blocking the main thread is to use `st.experimental_singleton` or
    # `st.experimental_memo` with a background thread, but your current `async def`
    # structure makes this harder without a more significant refactor.

    # To fix "not opening in a browser", ensure `asyncio.run` is *only* called
    # when you explicitly want to start the connection, and that the connection
    # loop can be exited gracefully.

    # A common (but still imperfect for truly continuous live data) Streamlit pattern:
    if st.session_state.is_connected:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_websocket_client())
        except asyncio.CancelledError:
            print("WebSocket task cancelled.")
        finally:
            loop.close()

    # The above `loop.run_until_complete` will still block.
    # The only way to make your current *structure* work non-blockingly for Streamlit
    # is to run the websocket_handler in a separate thread.

    # Here's a conceptual way using threading, which is better for this use case:
    # (You would need to pass data from the thread back to Streamlit using a queue)
    # import threading
    #
    # if "websocket_thread" not in st.session_state:
    #     st.session_state.websocket_thread = None
    # if "data_queue" not in st.session_state:
    #     import queue
    #     st.session_state.data_queue = queue.Queue()
    #
    # def run_websocket_in_thread(data_queue, is_connected_event):
    #     # Your run_websocket_client logic here, modified to put data into data_queue
    #     # and check is_connected_event.is_set() to stop
    #     # This part would be a bit more complex
    #     pass
    #
    # if st.session_state.is_connected and st.session_state.websocket_thread is None:
    #     st.session_state.is_connected_event = threading.Event()
    #     st.session_state.is_connected_event.set() # Set to True
    #     st.session_state.websocket_thread = threading.Thread(target=run_websocket_in_thread, args=(st.session_state.data_queue, st.session_state.is_connected_event))
    #     st.session_state.websocket_thread.start()
    #
    # # In your Streamlit app, you would then poll the data_queue for new data
    # # and update the plot.
    # # When 'Stop' is clicked, set st.session_state.is_connected_event.clear() and join the thread.
    #
    # # This is a significant architectural change.