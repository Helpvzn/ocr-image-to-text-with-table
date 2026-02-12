import streamlit as st
import os
import sys

# Fallback for OCR Engine (Moved up to prevent DLL conflict with cv2)
try:
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (PaddleOCR-main)
    parent_dir = os.path.dirname(current_dir)
    # Add the ocr_tool directory to the path
    ocr_tool_path = os.path.join(parent_dir, "ocr_tool")
    sys.path.insert(0, ocr_tool_path)
    from local_ocr_engine import LocalOCREngine
except Exception as e:
    st.error(f"OCR Engine not found in sibling directory: {e}")
    LocalOCREngine = None

import cv2
import numpy as np
import base64
import json
from PIL import Image

st.set_page_config(
    page_title="Vizan Designer Studio v2.0",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a professional dark workspace
st.markdown("""
<style>
    .stApp { background: #0e1117; color: #eee; }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }
    header { visibility: hidden; }
    .upload-box {
        text-align: center; padding: 60px; 
        background: #1a1c23; border: 2px dashed #4facfe; border-radius: 20px;
        margin: 100px auto; max-width: 700px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .stButton>button { border-radius: 8px; font-weight: 800; background: #4facfe; color: #fff; }
</style>
""", unsafe_allow_html=True)

# --- DESIGNER ENGINE INTERFACE (Fabric.js Core) ---
def serialize_numpy(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: serialize_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_numpy(i) for i in obj]
    return obj

def get_designer_v2(ocr_data, img_b64, w, h):
    ocr_json = json.dumps(serialize_numpy(ocr_data))
    
    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap" rel="stylesheet">
    <style>
        body {{ margin: 0; padding: 0; background: #000; font-family: 'Inter', sans-serif; overflow: hidden; }}
        #workspace {{ 
            width: 100vw; height: calc(100vh - 60px); 
            display: flex; align-items: flex-start; justify-content: center; 
            overflow: auto; margin-top: 60px; padding: 40px 20px;
        }}
        .canvas-container {{ 
            box-shadow: 0 0 100px rgba(0,0,0,1); 
            transition: transform 0.2s;
            transform-origin: center center;
        }}
        
        #toolbar {{ 
            position: fixed; top: 0; left: 0; right: 0; height: 60px; 
            background: #1a1a1a; display: flex; align-items: center; justify-content: space-between; 
            padding: 0 30px; border-bottom: 2px solid #333; z-index: 1000; 
        }}
        
        .v-logo {{ font-weight: 900; font-size: 22px; color: #4facfe; letter-spacing: -1px; }}
        .btn-pro {{ 
            background: #4facfe; color: #fff; border: none; padding: 10px 25px; 
            border-radius: 6px; cursor: pointer; font-weight: 900; font-size: 14px; 
            transition: 0.2s; margin-left: 8px;
        }}
        .btn-pro:hover {{ background: #008eff; transform: translateY(-1px); }}
        .btn-zoom {{ 
            background: #333; color: #fff; border: none; padding: 10px 15px; 
            border-radius: 6px; cursor: pointer; font-weight: 900; font-size: 18px; 
            transition: 0.2s; margin-left: 8px; width: 45px;
        }}
        .btn-zoom:hover {{ background: #555; }}

        #info-panel {{ 
            position: fixed; right: 25px; top: 85px; width: 240px; 
            background: rgba(26,26,26,0.95); border: 1px solid #444; border-radius: 12px; 
            padding: 20px; color: #eee; font-size: 13px; pointer-events: none; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
    </style>
</head>
<body>
    <div id="toolbar">
        <div class="v-logo">VIZAN <span style="color:#fff">STUDIO V2.1</span></div>
        <div style="display:flex; gap:5px; align-items:center">
            <button class="btn-zoom" onclick="zoomIn()">+</button>
            <button class="btn-zoom" onclick="zoomOut()">−</button>
            <span style="color:#888; margin:0 10px; font-size:13px" id="zoom-label">100%</span>
            <button class="btn-pro" onclick="downloadImage()">🖼️ PNG</button>
            <button class="btn-pro" onclick="downloadPDF()">📄 PDF</button>
            <button class="btn-pro" style="background:#333; color:#888" onclick="window.parent.location.reload()">EXIT</button>
        </div>
    </div>
    
    <div id="workspace">
        <canvas id="c"></canvas>
    </div>

    <div id="info-panel">
        <h4 style="margin:0 0 12px 0; color:#4facfe; font-size:15px">Designer Inspector</h4>
        <div style="line-height:1.8">
            <p>✅ <b>Double-Click</b>: Inline Edit</p>
            <p>✅ <b>Drag</b>: Reposition</p>
            <p>✅ <b>Zoom</b>: +/− Buttons</p>
            <p>✅ <b>Export</b>: PNG or PDF</p>
            <div style="margin-top:20px; border-top:1px dashed #444; padding-top:15px; opacity:0.6; font-style:italic">
                Engine: Fabric.js v5.3<br>
                Mode: Professional Studio
            </div>
        </div>
    </div>

    <script>
        const ocrData = {ocr_json};
        const canvas = new fabric.Canvas('c', {{
            width: {w},
            height: {h},
            backgroundColor: '#fff',
            preserveObjectStacking: true
        }});

        let currentZoom = 1;

        function fitToContainer() {{
            const pad = 120;
            const cw = window.innerWidth - pad;
            const ch = window.innerHeight - pad - 60;
            const scale = Math.min(cw / {w}, ch / {h}, 1);
            const outer = document.querySelector('.canvas-container');
            if(outer) outer.style.transform = 'scale(' + (scale * currentZoom) + ')';
        }}
        window.onresize = fitToContainer;

        function zoomIn() {{
            currentZoom = Math.min(currentZoom + 0.1, 2);
            fitToContainer();
            document.getElementById('zoom-label').innerText = Math.round(currentZoom * 100) + '%';
        }}

        function zoomOut() {{
            currentZoom = Math.max(currentZoom - 0.1, 0.5);
            fitToContainer();
            document.getElementById('zoom-label').innerText = Math.round(currentZoom * 100) + '%';
        }}

        fabric.Image.fromURL('data:image/jpeg;base64,{img_b64}', function(img) {{
            img.set({{ left: 0, top: 0, selectable: false, evented: false, opacity: 0.02 }});
            canvas.add(img);
            img.sendToBack();
            canvas.renderAll();
        }});

        if (ocrData && ocrData.processed_output) {{
            ocrData.processed_output.forEach(region => {{
                if(!region.lines) return;
                region.lines.forEach(line => {{
                    const b = line.bbox;
                    const boxHeight = b[3] - b[1];
                    const textBox = new fabric.Textbox(line.text, {{
                        left: b[0], 
                        top: b[1], 
                        width: Math.max(b[2] - b[0], 20),
                        fontSize: Math.max(boxHeight * 0.65, 8),
                        lineHeight: 0.9,
                        fontFamily: 'Inter, sans-serif', 
                        fill: '#000',
                        cornerColor: '#4facfe', 
                        cornerStrokeColor: '#fff', 
                        cornerSize: 10,
                        transparentCorners: false, 
                        selectable: true, 
                        editable: true,
                        borderColor: '#4facfe', 
                        borderDashArray: [5, 5],
                        padding: 2
                    }});
                    canvas.add(textBox);
                }});
            }});
        }}

        canvas.renderAll();
        fitToContainer();

        function downloadImage() {{
            const dataURL = canvas.toDataURL({{ format: 'png', quality: 1, multiplier: 3 }});
            const link = document.createElement('a');
            link.download = 'Vizan_Studio_Export.png';
            link.href = dataURL;
            link.click();
        }}

        function downloadPDF() {{
            const {{ jsPDF }} = window.jspdf;
            const imgData = canvas.toDataURL('image/jpeg', 1.0);
            
            const pdf = new jsPDF({{
                orientation: {w} > {h} ? 'landscape' : 'portrait',
                unit: 'px',
                format: [{w}, {h}]
            }});
            
            pdf.addImage(imgData, 'JPEG', 0, 0, {w}, {h});
            pdf.save('Vizan_Studio_Export.pdf');
        }}
    </script>
</body>
</html>
"""
    return html_template

# --- APP FLOW ---

if 'v2_state' not in st.session_state:
    st.session_state['v2_state'] = 'welcome'

def process_file(img):
    with st.spinner("AI is processing..."):
        try:
            engine = LocalOCREngine(use_gpu=False)
            results = engine.process_image(img)
            
            _, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            img_b64 = base64.b64encode(buffer).decode()
            
            st.session_state['v2_data'] = {
                'ocr': results,
                'image': img_b64,
                'w': results['metadata']['width'],
                'h': results['metadata']['height']
            }
            st.session_state['v2_state'] = 'studio'
            st.rerun()
        except Exception as e:
            st.error(f"Analysis Error: {e}")

if st.session_state['v2_state'] == 'welcome':
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
    st.title("🎨 Vizan Designer Studio v2.0")
    st.write("Professional Carbon-Copy Document Designer")
    
    up = st.file_uploader("Upload Document Image", type=['png', 'jpg', 'jpeg'])
    if up:
        f_bytes = np.asarray(bytearray(up.read()), dtype=np.uint8)
        img = cv2.imdecode(f_bytes, 1)
        if img is not None:
            if st.button("🚀 LAUNCH DESIGNER STUDIO"):
                process_file(img)
        else:
            st.error("Could not decode image. Please try another file.")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state['v2_state'] == 'studio':
    d = st.session_state['v2_data']
    from streamlit.components.v1 import html
    studio_html = get_designer_v2(d['ocr'], d['image'], d['w'], d['h'])
    html(studio_html, height=900, scrolling=False)
    
    # --- EDITOR & EXPORT SECTION ---
    st.markdown("---")
    st.subheader("📝 Edit Text & Regenerate Document")

    # Prepare data for editor
    raw_res = d['ocr'].get('raw_result', [])
    if raw_res and isinstance(raw_res, list) and len(raw_res) > 0:
        region = raw_res[0]
        lines_data = region.get('res', [])
        
        # Create a list of dictionaries for data_editor
        editor_data = []
        for i, line in enumerate(lines_data):
            editor_data.append({
                "ID": i + 1,
                "Text": line.get('text', '')
            })
            
        # Display Editor
        edited_data = st.data_editor(
            editor_data,
            column_config={
                "ID": st.column_config.NumberColumn(width="small", disabled=True),
                "Text": st.column_config.TextColumn(width="large")
            },
            use_container_width=True,
            hide_index=True,
            height=400,
            key=f"editor_{d['ocr']['metadata'].get('image_name')}"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
             if st.button("🔄 Generate Updated Word Doc", type="primary", use_container_width=True):
                 with st.spinner("Regenerating Document..."):
                     # Update the raw result with edited text
                     new_res = []
                     for i, row in enumerate(edited_data):
                         original_line = lines_data[i]
                         # Create copy of line with new text
                         new_line = original_line.copy()
                         new_line['text'] = row['Text']
                         new_res.append(new_line)
                         
                     # Construct new result structure
                     new_raw_result = [{
                         'type': region.get('type', 'text'),
                         'bbox': region.get('bbox'),
                         'res': new_res
                     }]
                     
                     # Re-initialize engine to call regeneration
                     try:
                         # Ensure LocalOCREngine is available
                         engine = LocalOCREngine(use_gpu=False)
                         
                         # Convert base64 image back to numpy for processing
                         nparr = np.frombuffer(base64.b64decode(d['image']), np.uint8)
                         img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                         
                         # Regenerate
                         new_doc_path = engine.regenerate_docx_from_result(
                             new_raw_result, 
                             img_np, 
                             img_name=f"edited_{d['ocr']['metadata'].get('image_name', 'doc')}"
                         )
                         
                         if new_doc_path:
                             st.success("✅ Document Updated!")
                             with open(new_doc_path, "rb") as f:
                                 st.download_button(
                                     label="📥 Download Edited Word Doc",
                                     data=f,
                                     file_name="Edited_Document.docx",
                                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                     use_container_width=True
                                 )
                         else:
                             st.error("Failed to regenerate document.")
                     except Exception as e:
                         st.error(f"Error during regeneration: {e}")

        with col2:
            if st.button("⬅️ New Project", use_container_width=True):
                st.session_state['v2_state'] = 'welcome'
                # Clear session state
                if 'v2_data' in st.session_state: del st.session_state['v2_data']
                st.rerun()

    else:
        st.warning("No editable text found.")
        if st.button("⬅️ New Project"):
            st.session_state['v2_state'] = 'welcome'
            st.rerun()
