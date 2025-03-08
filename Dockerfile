# Sử dụng hình ảnh Python làm hình ảnh cơ sở
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép tệp requirements.txt và cài đặt các thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng vào hình ảnh
COPY . .

# Thiết lập biến môi trường cho Flask
ENV FLASK_APP=app.py  
ENV FLASK_ENV=development

# Mở cổng 5000
EXPOSE 5000

# Chạy ứng dụng Flask
CMD ["flask", "run", "--host=0.0.0.0"]