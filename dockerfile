# ডিফল্ট ভ্যালু সেট করা ভালো যাতে বিল্ড করার সময় এরর না আসে
ARG AIRFLOW_VERSION=2.7.1
ARG PYTHON_VERSION=3.11

# এয়ারফ্লো এখনো অফিসিয়ালি পাইথন ৩.১৪ সাপোর্ট করে না, তাই ৩.১১ ব্যবহার করা নিরাপদ
FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# ENV ডিক্লেয়ার করার সময় ইকুয়াল চিহ্নের পাশে স্পেস রাখা যাবে না
ENV AIRFLOW_HOME=/opt/airflow

# রুট ইউজার হিসেবে ফাইল কপি এবং ইন্সটল করা নিরাপদ (যদি প্রয়োজন হয়)
USER root
COPY requirements.txt /requirements.txt

# এয়ারফ্লো ইউজার হিসেবে ফিরে আসা (বেস্ট প্র্যাকটিস)
USER airflow

# ইন্সটলেশন প্রসেস
RUN pip install --no-cache-dir -r /requirements.txt