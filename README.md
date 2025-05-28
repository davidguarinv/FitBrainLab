# Fit Brain Lab Website

Welcome to the Fit Brain Lab website! This is a web application that showcases research projects and provides interactive tools for our neuroscience and mental health research.

## 🚀 Getting Started

### Running the Website

1. **Start the Website:**
   ```bash
   python run.py
   ```
   
   This will start the website server. You can then access it by opening your web browser and going to `http://localhost:5000`.


## 📋 How to Update the Website

### 🏡 Adding New Content

1. **Research Projects**
   - Copy template from `templates/research/`
   - Update content sections:
     - Main description
     - Methodology
     - Project details
   - Add images to `static/images/`

2. **Communities**
   - Edit `static/data/communities.json`
   - Add entries with:
     - Name, Sport, Contact info
     - Location, Cost, Student-based
     - Logo URL

3. **Publications**
   - Edit `static/data/publications.json`
   - Add entries with:
     - Title, Authors, Journal
     - Year, DOI, Description
     - PDF path

### 🎮 Game Structure

- **Game Pages** (`templates/game.html`)
  - Main interface
  - Score tracking
  - Challenge system

- **Game Assets** (`static/`)
  - Media files
  - Challenge data

### 🎨 Styling and Design

- **Color Scheme**
  - Primary: Orange and Red gradients
  - Secondary: Yellow accents
  - Text: Slate colors

- **CSS Files**
  - Main styles in `static/css/output.css`
  - Use Tailwind CSS classes

### 📁 Project Structure

```
FitBrainLab/
├── app/                 # Python backend
├── static/              # Static files
│   ├── css/            # Stylesheets
│   ├── images/         # Project images
│   └── js/             # JavaScript
└── templates/          # HTML templates
    ├── research/       # Research pages
    ├── game/           # Game interface
    └── pages/          # Main pages
```

## 🛠️ Technical Details

- **Backend**: Flask framework
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: JSON files for content

## 📝 Best Practices

1. **Naming**
   - Use lowercase with hyphens
   - Descriptive filenames
   - Consistent patterns

2. **Images**
   - Optimize before upload
   - Descriptive filenames
   - Consistent sizes

3. **Content**
   - Use existing styling
   - Keep consistent formatting
   - Test all changes

## 🚀 Getting Started

```bash
# Clone repository
git clone https://github.com/davidguarinv/FitBrainLab.git

# Run development server
python run.py

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
