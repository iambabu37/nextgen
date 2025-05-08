import os
import subprocess
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views import View
from .models import UploadedFileFastQC
from django.views.decorators.clickjacking import xframe_options_sameorigin



def fastqc(request):
    """Render the home page for file upload."""
    return render(request, "fastqc/fastqc.html")

def upload_file(request):
    """Handle full-file uploads."""
    if request.method == 'POST':
        file = request.FILES.get('file')

        # Validate file type
        if not file or not file.name.endswith(('.fastq', '.fq', '.gz')):
            return JsonResponse({'error': 'Unsupported file type'}, status=400)

        # Save the uploaded file to the database
        uploaded_file = UploadedFileFastQC.objects.create(file=file)
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
        uploaded_file = UploadedFileFastQC.objects.create(file=file)
        return JsonResponse({'file_id': uploaded_file.id})

def run_fastqc_conda(file_path):
    """
    Run fastqc on the specified file using the 'fastqc_env' conda environment.
    Assumes conda is installed at ~/miniconda3 (adjust if different).
    """
    output_dir = os.path.dirname(file_path)
    html_report = os.path.join(output_dir, "fastqc.html")
    json_report = os.path.join(output_dir, "fastqc.json")

    # Construct the bash command string
    bash_command = f"""
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate fastqc_env
    fastqc -i "{file_path}" -o /dev/null --html "{html_report}" --json "{json_report}"
    conda deactivate
    """

    try:
        result = subprocess.run(
            bash_command,
            shell=True,
            executable="/bin/bash",
            check=True,
            capture_output=True,
            text=True
        )
        print("FastQC output:\n", result.stdout)
        return html_report

    except subprocess.CalledProcessError as e:
        print("Error running FastQC:", e.stderr)
        return None

def process_file(request, file_id):
    """Process the uploaded file with fastqc."""
    uploaded_file = get_object_or_404(UploadedFileFastQC, id=file_id)
    print("i am processing here")
    input_path = uploaded_file.file.path
    print(input_path)

    # Run fastp and save the HTML report path
    report_path = run_fastqc_conda(input_path)
    
    if not report_path:
        return JsonResponse({'error': 'Failed to generate report'}, status=500)

    # Update the result_html field with the report path
    uploaded_file.result_html.name = os.path.relpath(report_path, start='media/')
    uploaded_file.save()

    return redirect('result', file_id=file_id)

@xframe_options_sameorigin
def result_page(request, file_id):
    """Display the analysis result page."""
    print("ima in result page now")
    uploaded_file = get_object_or_404(UploadedFileFastQC, id=file_id)
    return render(request, 'fastqc/fastqcresult.html', {'file': uploaded_file})

def download_report(request, file_id):
    """Download the generated report."""
    uploaded_file = get_object_or_404(UploadedFileFastQC, id=file_id)
    
    # Ensure that the report exists before trying to open it
    if not uploaded_file.result_html or not os.path.exists(uploaded_file.result_html.path):
        return JsonResponse({'error': 'Report not found'}, status=404)

    return FileResponse(open(uploaded_file.result_html.path, 'rb'), as_attachment=True)
