from django.db import models

class UploadedFileFastP(models.Model):
    file = models.FileField(upload_to='uploads/fastp')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    result_html = models.FileField(upload_to='reports/fastp', blank=True, null=True)
