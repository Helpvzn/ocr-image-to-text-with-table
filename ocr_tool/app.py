import streamlit as st
import cv2
import numpy as np
import os
import textwrap
from PIL import Image
try:
    from local_ocr_engine import LocalOCREngine
except Exception as e:
    # If it still fails, show error in streamlit
    st.error(f"Failed to load OCR Engine: {e}")
    st.exception(e)
    LocalOCREngine = None

# Page Config
st.set_page_config(
    page_title="PaddleOCR Local - Premium",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Wow" factor
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main {
        background: #0e1117;
        color: #fafafa;
    }
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #ffffff;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }
    .stButton>button {
        color: #ffffff;
        background-color: #ff4b4b;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff6b6b;
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
    div[data-testid="stFileUploader"] {
        border: 2px dashed #4c4c4c;
        border-radius: 15px;
        padding: 20px;
        transition: border-color 0.3s;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #ff4b4b;
    }
    .ocr-result-box {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    table {
        width: 100%;
        border-collapse: collapse;
        color: #ddd;
        font-family: 'Courier New', monospace;
    }
    th, td {
        border: 1px solid #444;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #2b2b2b;
    }
    tr:nth-child(even) {
        background-color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://github.com/PaddlePaddle/PaddleOCR/raw/release/2.6/doc/paddleocr_logo.png", use_container_width=True)
    st.title("Settings")
    use_gpu = st.toggle("Use GPU", value=False)
    lang = st.selectbox("Language", ["en", "ch", "fr", "german", "korean", "japan"], index=0)
    
    st.markdown("---")
    st.info("This tool runs locally on your machine. Text and tables are extracted using PaddleOCR PP-Structure.")

# --- MAIN APPLICATION LOGIC ---
if 'ocr_result' in st.session_state:
    # PHASE 1: FULL-SCREEN DESIGNER STUDIO
    data = st.session_state['ocr_result']
    processed_output = data.get('processed_output', [])
    metadata = data.get('metadata', {})
    img_base64 = data.get('img_base64', "")

    img_w = metadata.get('width', 800)
    img_h = metadata.get('height', 1000)

    # --- THE ULTIMATE PROFESSIONAL STUDIO (POLOTNO-GRADE) ---
    html_template = """<style>
#vizan-studio-container {
position: fixed; top: 0; left: 0; right: 0; bottom: 0;
background: #000; z-index: 9999; display: flex; flex-direction: column; overflow: hidden;
font-family: 'Segoe UI', system-ui, sans-serif;
}
.v-topbar {
height: 64px; background: #1a1a1a; border-bottom: 2px solid #333;
display: flex; align-items: center; justify-content: space-between;
padding: 0 40px; color: #fff; z-index: 10001;
}
.v-logo { font-weight: 900; font-size: 20px; color: #4facfe; }
.btn-pro {
background: #4facfe; border: none; color: #fff; padding: 10px 30px;
border-radius: 6px; font-weight: 800; cursor: pointer; transition: 0.2s;
}
.v-body {
flex: 1; display: flex; align-items: center; justify-content: center;
position: relative; background: #111; background-image: radial-gradient(#262626 1px, transparent 1px); background-size: 24px 24px;
}
#konva-stage-container { background: #fff; box-shadow: 0 0 120px rgba(0,0,0,1); }
.v-panel {
position: absolute; right: 25px; top: 25px; width: 260px;
background: rgba(22,22,22,0.95); border: 1px solid #444; border-radius: 12px; padding: 25px;
color: #fff; font-size: 14px; pointer-events: none; z-index: 10002;
}
</style>
<div id="vizan-studio-container">
<div class="v-topbar">
<div class="v-logo">VIZAN <span style="color:#fff">STUDIO PRO v8.1</span></div>
<div style="display:flex; gap:15px; align-items:center">
<button onclick="window.downloadHighRes()" class="btn-pro">🖼️ Export Project</button>
<button onclick="location.reload()" style="background:none; border:none; color:#666; cursor:pointer; font-weight:700">EXIT</button>
</div>
</div>
<div class="v-body">
<div id="konva-stage-container"></div>
<div class="v-panel">
<h4 style="margin:0 0 15px 0; color:#4facfe; font-size:16px">Designer Inspector</h4>
<div style="line-height:2; opacity:0.9">
<p>✅ Studio Engine: Konva 9.3</p>
<p>✅ Interactivity: Enabled</p>
<div style="margin-top:20px; border-top:1px dashed #444; padding-top:15px">
<p>⌨️ <b>Dbl-Click</b> to Edit Text</p>
<p>🖱️ <b>Drag</b> to Reposition</p>
<p>📏 <b>Select</b> to Transform</p>
</div>
</div>
</div>
</div>
</div>
<script src="https://unpkg.com/konva@9.3.0/konva.min.js"></script>
<script>
(function() {
    // Start with a small delay to allow Streamlit containers to stabilize
    setTimeout(() => {
        try {
            const ocrData = REPLACEMENT_OCR_DATA;
            const imgData = "data:image/jpeg;base64,REPLACEMENT_IMG_BASE64";
            const w = REPLACEMENT_W, h = REPLACEMENT_H;

            const container = document.querySelector('.v-body');
            // Guaranteed dimensions via fallback
            const cw = container.offsetWidth || window.innerWidth;
            const ch = container.offsetHeight || window.innerHeight;
            const scale = Math.min((cw - 100) / w, (ch - 100) / h, 1) || 0.5;

            const stage = new Konva.Stage({
                container: 'konva-stage-container',
                width: w * scale, height: h * scale,
                scaleX: scale, scaleY: scale
            });

            const layer = new Konva.Layer();
            stage.add(layer);

            const tr = new Konva.Transformer({ padding: 5, anchorFill: '#fff', anchorStroke: '#4facfe', borderStroke: '#4facfe' });
            layer.add(tr);

            // 1. White Paper Foundation
            const bgRect = new Konva.Rect({ x: 0, y: 0, width: w, height: h, fill: '#fff' });
            layer.add(bgRect);

            // 2. Load Reference Image (guide)
            if(imgData.length > 100) {
                const img = new Image();
                img.onload = () => {
                    const kImg = new Konva.Image({ image: img, width: w, height: h, opacity: 0.1 });
                    layer.add(kImg);
                    kImg.moveToBottom();
                    bgRect.moveToBottom();
                    layer.draw();
                };
                img.src = imgData;
            }

            // 3. Render Interactive Text Items
            ocrData.forEach(region => {
                if(!region.lines) return;
                region.lines.forEach(line => {
                    const b = line.bbox;
                    const textNode = new Konva.Text({
                        x: b[0], y: b[1], text: line.text, width: Math.max(b[2]-b[0], 2),
                        fontSize: Math.max((b[3]-b[1]) * 0.95, 8),
                        fontFamily: 'Inter, sans-serif', fill: '#000', draggable: true
                    });
                    layer.add(textNode);

                    // Click to Select
                    textNode.on('mousedown touchstart', () => {
                        tr.nodes([textNode]);
                        layer.batchDraw();
                    });

                    // DblClick to Edit
                    textNode.on('dblclick dbltap', () => {
                        tr.nodes([]);
                        const pos = textNode.absolutePosition();
                        const sB = stage.container().getBoundingClientRect();
                        const ta = document.createElement('textarea');
                        document.body.appendChild(ta);
                        ta.value = textNode.text();
                        Object.assign(ta.style, {
                            position: 'absolute', top: (sB.top + pos.y) + 'px', left: (sB.left + pos.x) + 'px',
                            width: textNode.width() * scale + 'px', height: textNode.getSelfRect().height * scale + 'px',
                            fontSize: textNode.fontSize() * scale + 'px', zIndex: 20000,
                            border: '1px solid #4facfe', background: '#fff', outline: 'none', resize: 'none'
                        });
                        ta.focus();
                        ta.onblur = () => { textNode.text(ta.value); ta.remove(); layer.draw(); };
                        ta.onkeydown = (e) => { if(e.key === 'Enter' && !e.shiftKey) ta.blur(); if(e.key === 'Escape') ta.remove(); };
                    });
                });
            });

            layer.draw();
            stage.on('mousedown touchstart', (e) => { if(e.target===stage || e.target===bgRect) { tr.nodes([]); layer.batchDraw(); } });

            window.downloadHighRes = function() {
                tr.nodes([]); layer.draw();
                const lnk = document.createElement('a'); lnk.download = 'Vizan_Export.png';
                lnk.href = stage.toDataURL({ pixelRatio: 3 }); lnk.click();
            };
        } catch(e) { console.error('Studio Render Error:', e); }
    }, 100);
})();
</script>"""
    
    import json
    studio_html = html_template.replace("REPLACEMENT_OCR_DATA", json.dumps(processed_output)) \
                               .replace("REPLACEMENT_IMG_BASE64", img_base64) \
                               .replace("REPLACEMENT_W", str(img_w)) \
                               .replace("REPLACEMENT_H", str(img_h))

    st.markdown(studio_html, unsafe_allow_html=True)

else:
    # PHASE 2: UPLOAD & ANALYSIS UI
    st.title("📄 Intelligent Document Extraction")
    st.markdown("Upload a document, receipt, or invoice for **high-fidelity** interactive extraction.")
    uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'])

    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        
        st.markdown('<div style="text-align: center; margin-bottom: 20px;"><h3>📄 Document Ready</h3></div>', unsafe_allow_html=True)
        col_view = st.columns([1, 2, 1])
        with col_view[1]:
            st.image(image, channels="BGR", use_container_width=True)
            if st.button("🚀 Run AI Carbon Copy Analysis", type="primary", use_container_width=True):
                with st.spinner("Analyzing document structure..."):
                    try:
                        engine = LocalOCREngine(use_gpu=use_gpu, lang=lang)
                        result_data = engine.process_image(image, save_folder="output_results")
                        
                        # Fix: Store image base64 correctly for robust session recovery
                        import base64
                        _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                        img_base64 = base64.b64encode(buffer).decode()
                        
                        result_data['img_base64'] = img_base64
                        st.session_state['ocr_result'] = result_data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis Error: {e}")
    else:
        # Initial Welcome Screen
        st.markdown("""
        <div style='text-align: center; padding: 80px; color: #666; background: #1a1c23; border-radius: 20px; border: 2px dashed #444; margin-top: 30px;'>
            <h2 style="color: #fff;">👋 Welcome to Vizan Designer Studio</h2>
            <p style="font-size: 1.1em;">Please upload an image to begin your project.</p>
        </div>
        """, unsafe_allow_html=True)
