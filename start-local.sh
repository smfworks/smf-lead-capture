#!/bin/bash
# Start SMF Lead Capture server locally

cd /home/mikesai1/projects/smf-lead-capture
source venv/bin/activate

export PYTHONPATH=src:$PYTHONPATH
export FLASK_ENV=production

python -c "
import sys
sys.path.insert(0, 'src')
from smf_lead_capture.server import create_app
app = create_app('config.production.yaml')
print('Starting SMF Lead Capture server...')
print('Access at: http://localhost:5000')
print('API Health: http://localhost:5000/api/health')
app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
"
