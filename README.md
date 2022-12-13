# ifrs17-calculation-app
This repo serves to host the Python code for the IFRS 17 calculation app.

## How to use
1. Clone the repo
```git
git clone https://gitlab.com/patrickmoehrke/ifrs17-calculation-app.git
```
2. After entering the directory, create a virtual environment and activate it:
```
virtualenv venv
```
```
source venv/bin/activate
```
3. Install the dependencies:
```
pip install -r requirements.txt
```
4. Start the `streamlit` app, located in `app.py`:
```
streamlit run app.py
```

## TODO
- [ ] Add .py version of the code to run the class as a module -- CURRENTLY HOLD-OVER SOLUTION
- [x] Update Streamlit dashboard to meet requirements
