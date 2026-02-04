def layout(title: str, content: str) -> str:
    return f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}

        .step-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            text-decoration: none;
            color: inherit;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .step-card:hover {{
            border-color: #0cc0df;
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(12, 192, 223, 0.15);
        }}

        .step-card i {{
            font-size: 2.5rem;
            color: #0cc0df;
            margin-bottom: 1rem;
        }}

        .step-card h3 {{
            margin: 0.5rem 0;
            color: white;
        }}

        .step-card p {{
            color: #9ca3af;
            margin: 0;
            font-size: 0.95rem;
        }}

        .steps {{
            display: flex;
            justify-content: space-between;
            max-width: 400px;
            margin: 2rem auto;
            position: relative;
        }}

        .steps::before {{
            content: '';
            position: absolute;
            top: 24px;
            left: 50px;
            right: 50px;
            height: 2px;
            background: #374151;
            z-index: 1;
        }}

        .step {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #374151;
            color: #9ca3af;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            position: relative;
            z-index: 2;
            transition: all 0.3s;
        }}

        .step.active {{
            background: #0cc0df;
            color: white;
            transform: scale(1.1);
        }}

        button:focus, a:focus {{
            outline: 2px solid #0cc0df;
            outline-offset: 2px;
        }}
    </style>
</head>
<body>
    <nav class="container">
        <ul>
            <li><strong><i class="fas fa-hat-wizard"></i> Prompts Wizard</strong></li>
        </ul>
    </nav>
    </nav>
    <main class="container">
        {content}
    </main>
</body>
</html>'''
