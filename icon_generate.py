import math
from PIL import Image, ImageDraw, ImageFilter

def generate_improved_icon(output_ico_path="assets/icons/logo.ico"):
    # Render em 512x512 para máxima qualidade e suavização
    size = 512  
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base do Ícone (Design Moderno Dark Glassmorphism)
    pad = 20
    
    # Sombra externa suave
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([pad-4, pad-4, size-pad+4, size-pad+4], radius=90, fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    img.paste(shadow, (0, 0), shadow)

    # Corpo principal arredondado com moldura azul metálica
    body_box = [pad, pad, size - pad, size - pad]
    draw.rounded_rectangle(body_box, radius=85, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=6)

    # Borda interna sutil
    draw.rounded_rectangle([pad+8, pad+8, size-pad-8, size-pad-8], radius=78, fill=None, outline=(30, 41, 59, 255), width=3)

    # 2. Grelha de Engenharia (Estilo CAD)
    grid_glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid_glow)
    
    x_min, x_max = 90, 422
    y_min, y_max = 90, 422
    
    # Linhas secundárias
    for x in range(x_min, x_max + 1, 55):
        g_draw.line([(x, y_min), (x, y_max)], fill=(30, 58, 138, 120), width=3)
    for y in range(y_min, y_max + 1, 55):
        g_draw.line([(x_min, y), (x_max, y)], fill=(30, 58, 138, 120), width=3)

    # Eixos X e Y
    g_draw.line([(x_min, y_max), (x_max, y_max)], fill=(71, 85, 105, 255), width=6)
    g_draw.line([(x_min, y_min), (x_min, y_max)], fill=(71, 85, 105, 255), width=6)

    img.paste(grid_glow, (0, 0), grid_glow)

    # 3. Tira Almen (Base Metálica)
    strip_box = [x_min, y_max - 20, x_max, y_max + 10]
    draw.rounded_rectangle(strip_box, radius=6, fill=(100, 116, 139, 255), outline=(148, 163, 184, 255), width=3)

    # 4. Bocal e Esferas de Shot Peening (Efeito 3D)
    # Bocal/Nozzle no canto superior esquerdo
    nozzle_pts = [(x_min + 20, y_min + 30), (x_min + 90, y_min + 65), (x_min + 75, y_min + 90), (x_min + 5, y_min + 55)]
    draw.polygon(nozzle_pts, fill=(51, 65, 85, 255), outline=(148, 163, 184, 255))
    
    # Esferas metálicas a atingir a superfície
    shots = [
        (160, 190, 18),
        (210, 170, 22),
        (260, 210, 16),
        (190, 230, 20),
        (290, 150, 14),
        (230, 120, 12)
    ]
    
    for sx, sy, sr in shots:
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(203, 213, 225, 255), outline=(255, 255, 255, 255), width=3)
        hl_r = sr // 3
        draw.ellipse([sx - sr//2, sy - sr//2, sx - sr//2 + hl_r, sy - sr//2 + hl_r], fill=(255, 255, 255, 255))

    # Efeito de brilho/faísca de impacto
    spark_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sp_draw = ImageDraw.Draw(spark_img)
    impact_x, impact_y = 220, 280
    sp_draw.ellipse([impact_x-35, impact_y-35, impact_x+35, impact_y+35], fill=(251, 146, 60, 180))
    spark_img = spark_img.filter(ImageFilter.GaussianBlur(15))
    img.paste(spark_img, (0,0), spark_img)

    # 5. Curva de Saturação Exponencial (Néon Azul)
    curve_pts = []
    for px in range(x_min, x_max + 1):
        t = (px - x_min) / (x_max - x_min)
        val = 1 - math.exp(-4.2 * t)
        py = y_max - (val * (y_max - y_min - 40))
        curve_pts.append((px, py))

    # Brilho de Néon Externo da Curva
    glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.line(curve_pts, fill=(56, 189, 248, 255), width=24, joint="curve")
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(12))
    img.paste(glow_layer, (0, 0), glow_layer)

    # Linha principal da curva
    draw.line(curve_pts, fill=(14, 165, 233, 255), width=10, joint="curve")
    draw.line(curve_pts, fill=(224, 242, 254, 255), width=4, joint="curve")

    # 6. Indicador do Ponto de Saturação (Regra dos 10% T)
    target_x = x_min + int(0.35 * (x_max - x_min))
    t_val = 0.35
    target_y = y_max - ((1 - math.exp(-4.2 * t_val)) * (y_max - y_min - 40))

    # Marcador Dourado
    draw.ellipse([target_x - 16, target_y - 16, target_x + 16, target_y + 16], fill=(245, 158, 11, 255), outline=(254, 243, 199, 255), width=4)
    draw.ellipse([target_x - 6, target_y - 6, target_x + 6, target_y + 6], fill=(255, 255, 255, 255))
    draw.line([(target_x, target_y), (target_x, y_max)], fill=(245, 158, 11, 180), width=3)

    # Guardar como ICO multi-resolução
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico_path, format="ICO", sizes=sizes)
    print(f"Ícone '{output_ico_path}' gerado com sucesso!")

if __name__ == "__main__":
    generate_improved_icon("assets/icons/logo.ico")