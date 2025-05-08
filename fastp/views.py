import os
import subprocess
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views import View
from .models import UploadedFileFastP
from django.views.decorators.clickjacking import xframe_options_sameorigin



def fastp(request):
    """Render the home page for file upload."""
    return render(request, "fastp/fastp.html")

def upload_file(request):
    """Handle full-file uploads."""
    if request.method == 'POST':
        file = request.FILES.get('file')

        # Validate file type
        if not file or not file.name.endswith(('.fastq', '.fq', '.gz')):
            return JsonResponse({'error': 'Unsupported file type'}, status=400)

        # Save the uploaded file to the database
        uploaded_file = UploadedFileFastP.objects.create(file=file)
        return JsonResponse({'file_id': uploaded_file.id})
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

class UploadFileChunkedView(View):
    def setup(self, request, *args, **kwargs):
        # Ensure upload handlers are set early in the lifecycle
        if not hasattr(request, 'FILES'):
            request.upload_handlers = [TemporaryFileUploadHandler()]
        super().setup(request, *args, **kwargs)

    def post(self, request):
        """Handle POST request for file upload."""
        file = request.FILES.get('file')

        # Validate file type
        if not file or not file.name.endswith(('.fastq', '.fq', '.gz')):
            return JsonResponse({'error': 'Unsupported file type'}, status=400)

        # Save the uploaded file to the database
        uploaded_file = UploadedFileFastP.objects.create(file=file)
        return JsonResponse({'file_id': uploaded_file.id})

def run_fastp(file_path):
    """Run fastp on the uploaded file and generate reports."""
    output_dir = os.path.dirname(file_path)
    html_report = os.path.join(output_dir, "fastp.html")
    
    # Construct command to run fastp
    command = f"fastp -i {file_path} -o /dev/null --html {html_report} --json {output_dir}/fastp.json"
    
    # Execute the command and check for errors
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running fastp: {e}")
        return None  # Return None if fastp fails
    
    return html_report

def process_file(request, file_id):
    """Process the uploaded file with fastp."""
    uploaded_file = get_object_or_404(UploadedFileFastP, id=file_id)
    input_path = uploaded_file.file.path

    # Run fastp and save the HTML report path
    report_path = run_fastp(input_path)
    
    if not report_path:
        return JsonResponse({'error': 'Failed to generate report'}, status=500)

    # Update the result_html field with the report path
    uploaded_file.result_html.name = os.path.relpath(report_path, start='media/')
    uploaded_file.save()

    return redirect('result', file_id=file_id)

@xframe_options_sameorigin
def result_page(request, file_id):
    """Display the analysis result page."""
    uploaded_file = get_object_or_404(UploadedFileFastP, id=file_id)
    return render(request, 'fastp/fastpresult.html', {'file': uploaded_file})

def download_report(request, file_id):
    """Download the generated report."""
    uploaded_file = get_object_or_404(UploadedFileFastP, id=file_id)
    
    # Ensure that the report exists before trying to open it
    if not uploaded_file.result_html or not os.path.exists(uploaded_file.result_html.path):
        return JsonResponse({'error': 'Report not found'}, status=404)

    return FileResponse(open(uploaded_file.result_html.path, 'rb'), as_attachment=True)
