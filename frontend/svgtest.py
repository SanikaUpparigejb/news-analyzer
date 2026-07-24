import streamlit as st
import base64

st.write("Test: base64-encoded SVG via img tag")

svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
     fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-11a1 1 0 0 1 1 -1h3" />
  <path d="M8 4h8v4h-8z" />
  <path d="M8 11h8" />
  <path d="M8 15h8" />
</svg>'''
b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")

st.html(f'''
<div style="width:60px;height:60px;background:#11173D;border-radius:12px;
            display:flex;align-items:center;justify-content:center;">
  <img src="data:image/svg+xml;base64,{b64}" width="28" height="28" />
</div>
''')