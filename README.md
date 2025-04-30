## Sarkari Parcha Parser - Quick Look 📄✨



It's a simple web tool that lets you upload your `.docx` file, tell it how many questions *should* be there, and BAM! It'll give you a quick rundown:

- How many questions it found.
- How many options it thinks are there (it kinda guesses based on the questions).
- The count of answers it spotted.
- And even the number of solutions it located.

Plus, it gives you a little preview of your document so you can see what's what. Think of it as a quick sanity check for your important documents.

### How to Use? 🤔

1.  **Grab your `.docx` file.** You know, the one you want to check.
2.  **Head over to the website** (once you get it running, that is 😉).
3.  **Upload your file.** There's a neat drag-and-drop area or a button to browse.
4.  **Tell it how many questions you *expect* to see.** Just type the number in.
5.  **Hit "Upload & Validate Document".**
6.  **Boom!** You'll see a summary of what it found, compared to what you expected. Green checkmarks are good, red 'X's mean something might be off. You'll also get a peek at your document's content.

### What's Under the Hood? ⚙️

This thingamajig is built with:

-   **Python** on the backend doing all the heavy lifting.
-   **Flask**, a cool little web framework for making it all interactive.
-   **`python-docx`** to actually read and understand your `.docx` files.
-   **Tailwind CSS** to make it look kinda nice and clean without too much fuss.

It even tries to be a bit smart about images in your document and shows them in the preview!

### Running it Yourself? 💻

If you're the techy type and wanna run this on your own machine, here's the super quick version:

1.  **Make sure you've got Python installed.** If not, go grab it from [python.org](https://www.python.org/).
2.  **Clone this repository** (if you got the code from somewhere like GitHub).
3.  **Install the necessary libraries.** Open your terminal or command prompt, navigate to the project folder, and run:
    ```bash
    pip install flask python-docx
    ```
4.  **Run the app!** In the same terminal, just type:
    ```bash
    python app.py
    ```
    (Assuming your Python file is named `app.py` - which it is in this case!)
5.  **Open your browser** and go to `http://127.0.0.1:5000/`. You should see the tool up and running.

### Just a Heads Up! 📢

-   This is a pretty basic tool right now. It counts things based on some simple patterns (like lines starting with "Q", "a.", "Ans.", "Sol."). It's not gonna be perfect for every single document format out there.
-   The "options found" is a bit of a guess – it just multiplies the number of questions by four. So, if your options aren't always in that exact pattern, it might not be spot on.
-   It's all happening in memory right now. So, when you close the tool, the uploaded files are gone.

### Future Ideas? 🤔💡

Maybe someday it could:

-   Be smarter about identifying options, not just guessing.
-   Handle different document formats.
-   Give more detailed feedback on the document structure.
-   Let you download a report.

But for now, it's a handy little tool for a quick check. Enjoy! 😊
