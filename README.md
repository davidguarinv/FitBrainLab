# Fit Brain Lab Website

Welcome to the Fit Brain Lab website! This is a web application that showcases research projects and provides interactive tools for our neuroscience and mental health research.

## 🚀 Getting Started

### Running the Website

1. **Start the Website:**
   ```bash
   python run.py
   ```
   
   This will start the website server. You can then access it by opening your web browser and going to `http://localhost:5000`.

### Project Structure Overview

The website is organized into several key directories:

- `templates/`: Contains all HTML files that make up the website pages
- `static/`: Contains images, CSS, and JavaScript files
- `app/`: Contains the Python backend code

## 📋 Updating Website Content

### Updating Research Project Pages

1. **Find the Project Template:**
   Each research project has its own template file in the `templates/research/` directory (e.g., `brain_adaptations.html`, `leopard_predict.html`).

2. **Update Text Content:**
   - Project descriptions are in the main content section
   - Methodology lists are in the "Research Methodology" section
   - Project details are in the sidebar

3. **Updating Images:**
   - Place new images in the `static/images/` folder
   - Reference them in templates using this format: `{{ url_for('static', filename='images/your_image.png') }}`
   - Make sure images are properly sized and named appropriately

### Common Template Sections

1. **Project Overview:**
   - Located in the main content section
   - Contains the main description of the project
   - Should be concise but informative

2. **Research Methodology:**
   - Contains bullet points with icons
   - Each point should describe a specific research technique
   - Icons are SVGs that can be replaced if needed

3. **Project Details Sidebar:**
   - Contains status, timeline, model, and focus information
   - Also lists project partners
   - Each item is in a colored box with a different color scheme

## 🛠️ Technical Details

### Dependencies

The project uses several Python packages listed in `requirements.txt`. These include:
- Flask for the web framework
- SQLAlchemy for database management
- Other web development tools

### Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📝 Best Practices for Content Updates

1. **Text Updates:**
   - Keep descriptions concise and focused
   - Use consistent formatting across projects
   - Maintain proper grammar and spelling

2. **Image Updates:**
   - Use appropriate image sizes (typically 1200x630px for featured images)
   - Ensure images are optimized for web
   - Use descriptive filenames

3. **Consistency:**
   - Maintain consistent color schemes
   - Follow existing template structures
   - Keep similar formatting across all pages

## 🤝 Contributing

When making changes:
1. Backup your files before major changes
2. Test changes locally before deployment
3. Follow the existing template patterns
4. Document any major changes in this README

## 📱 Contact

For technical questions or help with updates, please contact the project maintainer.
