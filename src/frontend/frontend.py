import os
import subprocess

def main():
    streamlit_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'streamlit.py'))

    # Ensure the path ends with .py
    if not streamlit_script_path.endswith('.py'):
        raise ValueError("The Streamlit script path must end with .py")

    print(f"Running Streamlit application at: {streamlit_script_path}")

    # Run the Streamlit application
    try:
        result = subprocess.run(["streamlit", "run", streamlit_script_path], check=True, text=True, capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        print(f"Error output: {e.stderr}")
if __name__ == "__main__":
    main()
