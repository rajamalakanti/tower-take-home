# README

## Setup Instructions

Follow these steps to set up the environment and run the script to generate a book report using a language model.

### 1. Clone the Repository
First, clone the repository from GitHub:
```sh
git clone https://github.com/rajamalakanti/tower-take-home.git
```

### 2. Navigate to the Project Directory
Move into the `deliverables` folder:
```sh
cd deliverables
```

### 3. Create a Virtual Environment
To avoid dependency conflicts, create a virtual environment:
```sh
python3 -m venv venv
```

### 4. Activate the Virtual Environment
#### On macOS/Linux:
```sh
source venv/bin/activate
```
#### On Windows:
```sh
venv\Scripts\activate
```

### 5. Install Dependencies
Once the virtual environment is activated, install all required dependencies:
```sh
pip install -r requirements.txt
```

### 6. Navigate to the `code` Directory
Change into the `code` directory where the scripts are located:
```sh
cd code
```

### 7. Configure API Keys
Copy and paste the necessary API keys into the `.env` file. Make sure API keys are all right, find them in the password protected pdf attatched in the email submission.

### 8. Run the Script
Execute the main script to process the books and generate the report:
```sh
python3 main.py
```

### 9. Happy Reading!
Once the script completes execution, you should have a fully generated book report. Enjoy reviewing the insights provided by the language model!
