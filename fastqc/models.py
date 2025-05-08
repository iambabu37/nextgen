from django.db import models

class UploadedFileFastQC(models.Model):
    file = models.FileField(upload_to='uploads/fastq/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    result_html = models.FileField(upload_to='reports/fastq/', blank=True, null=True)
