# 1. Use an official, lightweight Python image
FROM python:3.14-slim

# 2. Set environment variables to optimize Python inside the container
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy the requirements file and install dependencies
# (This ensures Docker caches your pip packages unless requirements.txt changes)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your root directory code into the container
COPY . /app/

#THIS LINE Collects all static files into your production directory
RUN python EBIL_CLAIMS/manage.py collectstatic --noinput

# 6. Expose the port Django runs on
EXPOSE 8000

# 7. Command to run the Django development server
CMD ["python", "EBIL_CLAIMS/manage.py", "runserver", "0.0.0.0:8000"]
