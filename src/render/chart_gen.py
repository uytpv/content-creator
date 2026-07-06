import matplotlib
matplotlib.use('Agg') # Tránh bật cửa sổ UI GUI khi vẽ ở nền
import matplotlib.pyplot as plt

def generate_chart_image(chart_data: dict, output_path: str):
    """
    Vẽ biểu đồ hình cột (Bar Chart) nghệ thuật chủ đề Dark Mode
    phục vụ chèn vào video phân cảnh.
    """
    title = chart_data.get("title", "Statistics")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    
    # Thiết lập cấu hình Style Dark Mode cao cấp
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    
    # Màu nền slate tối sang trọng đồng nhất với Web UI
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#1e293b')
    
    # Màu cột dải gradient tím/indigo nghệ thuật
    colors = ['#818cf8', '#c084fc', '#fb7185', '#34d399'][:len(labels)]
    if len(colors) < len(labels):
        colors = colors * (len(labels) // len(colors) + 1)
        colors = colors[:len(labels)]
        
    bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor='rgba(255,255,255,0.1)', linewidth=1.5)
    
    # Định dạng nhãn và lưới
    ax.tick_params(colors='#e2e8f0', labelsize=18)
    ax.grid(color='rgba(255,255,255,0.05)', linestyle='--', linewidth=1)
    ax.set_axisbelow(True)
    
    # Bỏ viền khung biểu đồ cho thoáng mắt
    for spine in ['top', 'right', 'left', 'bottom']:
        ax.spines[spine].set_visible(False)
        
    # Thêm số liệu trực tiếp trên đầu mỗi cột
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 8),  # dịch lên 8pt
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=20, color='#f8fafc', weight='bold')
                    
    # Tiêu đề biểu đồ nổi bật
    plt.title(title, fontsize=28, color='#f1f5f9', pad=40, weight='bold', family='sans-serif')
    
    # Căn lề vừa khít
    plt.tight_layout()
    
    # Lưu ảnh 1080p
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close()
    print(f"Chart image rendered and saved to: {output_path}")
