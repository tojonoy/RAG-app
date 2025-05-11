web: honcho start
fastapi: gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
streamlit: streamlit run stream.py --server.port=$PORT --server.address=0.0.0.0
