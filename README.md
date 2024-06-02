# Properties Visualizer

This project consists of two main parts: a Flask API and a React application. The Flask API processes XML files, stores the data in a SQLite database, and provides endpoints to retrieve this data. The React application fetches and displays the data stored in the SQLite database.

## Prerequisites

- Python 3.x
- Node.js
- npm (Node Package Manager)

## Setting Up the Flask API

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/properties-visualizer.git
cd properties-visualizer
```
### 2. Set Up a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```
### 3. Install Dependencies

```bash
pip install flask flask-cors requests
```