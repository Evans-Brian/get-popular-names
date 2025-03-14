# PowerShell script to deploy the Lambda function

# Ensure AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Cyan
$awsConfig = aws configure list
if ($LASTEXITCODE -ne 0) {
    Write-Host "AWS CLI is not configured properly. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Install required Python packages if not already installed
Write-Host "Installing required Python packages..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install required Python packages. Please check requirements.txt." -ForegroundColor Red
    exit 1
}

# Run the deployment script
Write-Host "Running deployment script..." -ForegroundColor Cyan
python create_deployment.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed. Please check the error messages above." -ForegroundColor Red
    exit 1
}

Write-Host "Deployment process completed successfully!" -ForegroundColor Green
Write-Host "The Lambda function now supports both direct invocation and API Gateway integration." -ForegroundColor Green
Write-Host "Test results have been saved to:" -ForegroundColor Green
Write-Host "  - output-direct.json (Direct invocation)" -ForegroundColor Green
Write-Host "  - output-api.json (API Gateway event)" -ForegroundColor Green 