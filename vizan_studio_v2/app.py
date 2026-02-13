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
import pandas as pd
import io

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
            <button class="btn-pro" onclick="copyText()">📋 COPY</button>
            <button class="btn-pro" style="background:#333; color:#888" onclick="window.parent.location.reload()">EXIT</button>
        </div>
    </div>
    
    <div id="workspace">
        <canvas id="c"></canvas>
    </div>

    <!-- Inspector Removed as per user request -->
    <!--
    <div id="info-panel">
        <h4 style="margin:0 0 12px 0; color:#4facfe; font-size:15px">Designer Inspector</h4>
        ...
    </div>
    -->

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

        function copyText() {{
            let allText = [];
            canvas.getObjects().forEach(obj => {{
                if (obj.text) allText.push(obj.text);
            }});
            const textToCopy = allText.join('\\n');
            navigator.clipboard.writeText(textToCopy).then(() => {{
                alert('Text Copied to Clipboard! 📋');
            }}).catch(err => {{
                console.error('Failed to copy: ', err);
            }});
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

    # --- ACTION BUTTONS & PREVIEW ---
    st.markdown("---")
    
    raw_res = d['ocr'].get('raw_result', [])
    docx_path = d['ocr'].get('docx_path')
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if docx_path and os.path.exists(docx_path):
            with open(docx_path, "rb") as f:
                st.download_button(
                    label="📥 Download Original Word Doc",
                    data=f,
                    file_name=os.path.basename(docx_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    type="primary"
                )
        else:
            st.info("Word Document not available.")
            
    with c2:
        if st.button("⬅️ New Project", use_container_width=True):
            st.session_state['v2_state'] = 'welcome'
            if 'v2_data' in st.session_state: del st.session_state['v2_data']
            st.rerun()

    # --- FORMATTED PREVIEW ---
    if raw_res and isinstance(raw_res, list) and len(raw_res) > 0:
        st.markdown("---")
        st.subheader("📄 Formatted Document Preview")
        st.caption("Select content below to Copy (Maintains Layout & Tables) 📋")
        
        # Determine scale for preview (fit to ~800px width)
        orig_w = d['w']
        orig_h = d['h']
        target_w = 800
        scale = target_w / orig_w if orig_w > 0 else 1.0
        target_h = int(orig_h * scale)
        
        preview_html = ""
        
        # Sort regions for DOM order
        sorted_regions = sorted(raw_res, key=lambda x: (x['bbox'][1] if x.get('bbox') else 0, x['bbox'][0] if x.get('bbox') else 0))
        
        for region in sorted_regions:
            bbox = region.get('bbox') # [x1, y1, x2, y2]
            if not bbox: continue
            
            x, y = bbox[0] * scale, bbox[1] * scale
            w, h = (bbox[2] - bbox[0]) * scale, (bbox[3] - bbox[1]) * scale
            
            rtype = region.get('type')
            res = region.get('res')
            
            if rtype == 'table':
                if isinstance(res, dict) and 'html' in res:
                     # Tables are tricky with absolute pos if they span huge areas.
                     # Render table in a div at its position.
                     # Remove html/body tags
                     t_html = res['html'].replace('<html><body>', '').replace('</body></html>', '')
                     # Styling
                     t_html = t_html.replace('<table', '<table style="width:100%; height:100%; border-collapse:collapse; font-size:12px;"')
                     t_html = t_html.replace('<td', '<td style="border:1px solid #ccc; padding:2px;"')
                     
                     preview_html += f'<div style="position:absolute; left:{x}px; top:{y}px; width:{w}px; overflow:hidden;">{t_html}</div>'
            else:
                # Text Region: Iterate over individual lines for exact positioning
                lines = region.get('res', [])
                if isinstance(lines, list):
                    for line in lines:
                        # Ensure line has bbox
                        l_bbox = line.get('bbox')
                        txt = line.get('text', '')
                        
                        if l_bbox and len(l_bbox) == 4 and txt.strip():
                            # Scale coordinates
                            lx, ly = l_bbox[0] * scale, l_bbox[1] * scale
                            lw, lh = (l_bbox[2] - l_bbox[0]) * scale, (l_bbox[3] - l_bbox[1]) * scale
                            
                            # Font estimation logic (approximate)
                            # Using height as guide
                            font_size = max(10, int(lh * 0.75))
                            
                            # Render line as absolute div
                            preview_html += f'<div style="position:absolute; left:{lx}px; top:{ly}px; width:{lw}px; height:{lh}px; font-size:{font_size}px; line-height:1; overflow:hidden; white-space:pre; font-family:Arial, sans-serif;">{txt}</div>'

        # Render HTML Container with ID and Toolbar
        # We need JS libraries for HTML to Image/PDF: html2canvas & jspdf
        # Since these might not be loaded in the main app context (outside get_designer_v2), we reinject them here just in case.
        # But script tags in st.markdown work.
        
        toolbar_html = f"""
        <div style="margin-bottom: 10px; display: flex; gap: 10px;">
            <button onclick="downloadPreviewImage()" style="padding: 5px 10px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px;">🖼️ Download PNG</button>
            <button onclick="downloadPreviewPDF()" style="padding: 5px 10px; cursor: pointer; background: #dc3545; color: white; border: none; border-radius: 4px;">📄 Download PDF</button>
        </div>
        """
        
        js_logic = """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
        <script>
            function downloadPreviewImage() {
                const element = document.getElementById('preview-container');
                html2canvas(element, { scale: 2 }).then(canvas => {
                    const link = document.createElement('a');
                    link.download = 'document_preview.png';
                    link.href = canvas.toDataURL();
                    link.click();
                });
            }
            
            async function downloadPreviewPDF() {
                const element = document.getElementById('preview-container');
                const canvas = await html2canvas(element, { scale: 2 });
                const imgData = canvas.toDataURL('image/png');
                
                const { jsPDF } = window.jspdf;
                const pdf = new jsPDF('p', 'mm', 'a4');
                const imgProps = pdf.getImageProperties(imgData);
                const pdfWidth = pdf.internal.pageSize.getWidth();
                const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
                
                pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
                pdf.save("document_preview.pdf");
            }
        </script>
        """
        
        st.markdown(
            f'''
            {js_logic}
            {toolbar_html}
            <div id="preview-container" style="position:relative; width:{target_w}px; height:{target_h}px; background:white; color:black; border:1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin: 0 auto; overflow:hidden;">
                {preview_html}
            </div>
            ''',
            unsafe_allow_html=True
        )

    else:
        st.warning("No editable text found.")
        if st.button("⬅️ New Project"):
            st.session_state['v2_state'] = 'welcome'
            st.rerun()
