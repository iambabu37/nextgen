
from django.urls import path
from .views import fastqc, UploadFileChunkedView, process_file, result_page, download_report,upload_file

urlpatterns = [
    path('', fastqc, name='fastqc'),  # Home page for uploading files
    path('upload/', upload_file, name='upload_file'),
    path('upload-chunked/', UploadFileChunkedView.as_view(), name='upload_chunked'),  # Chunked upload view
    path('process/<int:file_id>/', process_file, name='process_file'),  # Process uploaded files
    path('result/<int:file_id>/', result_page, name='result'),  # View analysis results
    path('download/<int:file_id>/', download_report, name='download_report'),  # Download report
]
