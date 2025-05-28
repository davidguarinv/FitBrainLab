# Fit Brain Lab Website

Welcome to the Fit Brain Lab website! This is a web application that showcases research projects and provides interactive tools for our neuroscience and mental health research.

## 🚀 Getting Started

### Running the Website

To start the development server:

```bash
# Clone the repository
git clone https://github.com/davidguarinv/FitBrainLab.git
cd FitBrainLab

# Run the development server
python run.py
```

Then open your browser and go to `http://localhost:5000`.

---

## 🛠️ Technical Details

### Dependencies

The project uses several Python packages listed in `requirements.txt`, including:

* **Flask** – for the web framework
* **SQLAlchemy** – for database management
* Other supporting web development tools

### Environment Setup

1. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
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
  - Primary Lab Information: Blue, Purple, Teal gradients
  - Primary Communities and Game: Orange and Red gradients
  - Text: Slate colors

- **CSS Files**
  - Mostly inline Tailwind CSS classes
  - Other standardized styles in `static/css/input.css` and `static/css/config/tailwind.config.js`


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


## 🤝 Contributing

When making changes:
1. Backup your files before major changes
2. Test changes locally before deployment
3. Follow the existing template patterns
4. Document any major changes in this README

## 📱 Contact

For technical questions or help with updates, please contact the project maintainer.
