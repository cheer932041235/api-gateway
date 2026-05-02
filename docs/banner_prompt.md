Create a professional technical architecture diagram for an open-source project called "API Gateway". This is a README banner image for GitHub.

The diagram shows how the API Gateway proxy sits between AI coding tools (clients) and multiple model providers, handling protocol translation automatically.

**IMPORTANT**: All pixel coordinates below are INTERNAL LAYOUT GUIDES only. Do NOT render any coordinates, pixel values, or axis labels as visible text.

## MODULE 1: GLOBAL CANVAS & LAYOUT GRID

- Canvas size: 1800 × 700 pixels, aspect ratio 2.57:1, white background
- Global margins: 40 px on all sides
- Primary flow axis: LEFT → RIGHT
- 3-column layout with generous spacing:
  - Col 1 – CLIENTS (narrow column, left ~20%): fill none
  - Col 2 – GATEWAY (medium column, center ~35%): subtle #FFF7ED background panel
  - Col 3 – PROVIDERS (wide column, right ~35%): fill none
- Inter-column gutter: 60 px
- Title band: top center, "API Gateway" in 36pt bold #1F2937, subtitle "Multi-Provider Proxy for AI Coding Tools" in 16pt regular #6B7280
- Z-order: background z=0, panels z=1, boxes z=2, arrows z=3, text z=4
- Style: Flat NeurIPS/ICLR style, no gradients, no shadows, no 3D, no textures. Professional pastel palette. Thin line weights (1.5px). Rounded rectangles for all blocks. Clean arrows with small arrowheads. Pure white background.
- ALL text must be in English only.

## MODULE 2: CLIENT BLOCKS (Left column)

Two vertically stacked rounded rectangles, evenly spaced:

- Block A: "Claude Desktop" — 200×100 px, fill #EDE9FE, stroke #7C3AED at 1.5pt, corner radius 12px
  - Icon area: small desktop monitor icon suggestion (simple line art)
  - Text: "Claude Desktop" in 13pt bold #5B21B6, centered
  - Subtext: "3P Mode" in 10pt regular #7C3AED

- Block B: "Codex CLI / Claude Code" — 200×100 px, fill #EDE9FE, stroke #7C3AED at 1.5pt, corner radius 12px
  - Icon area: small terminal icon suggestion (simple "> _" symbol)
  - Text: "Codex CLI" in 13pt bold #5B21B6, centered
  - Subtext: "Claude Code" in 10pt regular #7C3AED

Both blocks have right-edge arrow anchors.

## MODULE 3: GATEWAY CORE (Center column)

A large rounded rectangle panel: 450×400 px, fill #FFF7ED, stroke #F97316 at 2pt, corner radius 16px

- Header band: full width × 50px, fill #F97316, white text "API Gateway" in 16pt bold, centered
- Inside the panel, two sub-blocks stacked vertically:

  Sub-block A: "proxy.py" — 380×120 px, fill #FED7AA, stroke #EA580C at 1.5pt, corner radius 10px
  - Text: "proxy.py" in 14pt bold #9A3412
  - Subtext: "Claude Desktop Gateway :8082" in 10pt #EA580C
  - Badge: "Protocol Translation" in 9pt, pill shape, fill #FDBA74, text #9A3412

  Sub-block B: "codex-proxy.py" — 380×120 px, fill #FED7AA, stroke #EA580C at 1.5pt, corner radius 10px
  - Text: "codex-proxy.py" in 14pt bold #9A3412
  - Subtext: "Codex CLI Proxy :5678" in 10pt #EA580C
  - Badge: "Anthropic ↔ OpenAI" in 9pt, pill shape, fill #FDBA74, text #9A3412

  Between sub-blocks: small "Control Panel :8083" label in 9pt italic #B45309

## MODULE 4: PROVIDER BLOCKS (Right column)

Three vertically stacked rounded rectangles:

- Block A: "SophNet" — 220×80 px, fill #D1FAE5, stroke #059669 at 1.5pt, corner radius 10px
  - Text: "SophNet" in 13pt bold #065F46
  - Subtext: "DeepSeek, Kimi, GLM..." in 9pt #059669

- Block B: "aiproxies.cc" — 220×80 px, fill #D1FAE5, stroke #059669 at 1.5pt, corner radius 10px
  - Text: "aiproxies.cc" in 13pt bold #065F46
  - Subtext: "GPT-5.5, GPT-4o..." in 9pt #059669

- Block C: "Xiaomi MiMo" — 220×80 px, fill #D1FAE5, stroke #059669 at 1.5pt, corner radius 10px
  - Text: "Xiaomi MiMo" in 13pt bold #065F46
  - Subtext: "MiMo-V2.5-Pro..." in 9pt #059669

All blocks have left-edge arrow anchors.

## MODULE 5: GLOBAL ARROW ROUTING

- Arrow 1: Client Block A (right edge) → Gateway sub-block A (left edge), horizontal, 1.5pt solid, #7C3AED, small arrowhead
  - Label on arrow: "Anthropic API" in 9pt #6B7280, positioned above the arrow line

- Arrow 2: Client Block B (right edge) → Gateway sub-block B (left edge), horizontal, 1.5pt solid, #7C3AED, small arrowhead
  - Label on arrow: "Anthropic API" in 9pt #6B7280

- Arrow 3: Gateway sub-block A (right edge) → Provider Block A (left edge), 1.5pt solid, #059669, arrowhead
  - Label: "passthrough" in 8pt #6B7280

- Arrow 4: Gateway sub-block A (right edge) → Provider Block B (left edge), 1.5pt solid, #059669, arrowhead
  - Label: "translated" in 8pt #6B7280

- Arrow 5: Gateway sub-block A (right edge) → Provider Block C (left edge), 1.5pt solid, #059669, arrowhead

- Arrow 6: Gateway sub-block B (right edge) → Provider Block B (left edge), 1.5pt dashed, #059669, arrowhead
  - Label: "Anthropic → OpenAI" in 8pt #6B7280

All arrows are clean, horizontal or with minimal bends. No crossing arrows.
