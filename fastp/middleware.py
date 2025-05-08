from django.core.files.uploadhandler import TemporaryFileUploadHandler

class SetUploadHandlersMiddleware:
    """
    Middleware to set custom upload handlers before processing the request.
    This ensures that large files are handled efficiently and avoids errors
    when modifying upload handlers after processing has started.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set upload handlers before processing the request
        if request.method == "POST":
            request.upload_handlers = [TemporaryFileUploadHandler()]
        response = self.get_response(request)
        return response
