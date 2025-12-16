# Team 12470 Content Hub

### Project Info
* **Team Members:** Mathew Davis, Daniel Bernal, Leo Prissberg, Naomi Lopez, Alexander Trujillo, 
* **Class:** CST 205
* **Date:** Nov-Dec, 2025
* **GitHub Repository:** https://github.com/MatthewDDavis500/Team_12470_ContentHub

### Description
Content Hub is a customizable web dashboard built with Flask and MySQL. It allows users to create a secure account, log in, and curate a personal dashboard. The application currently includes the following interactive widgets:
* **Weather & News:** Real-time updates based on your preferences.
* **MiniPlayer:** A Spotify integration to search and launch songs.
* **Bitcoin Tracker:** Live price updates for BTC.
* **Pokemon Tools:** Search for Pokemon or generate random ones.
* **Image Filter:** Upload images and apply effects like grayscale or sepia.
* **Book Search:** Find books in the public domain.
* **Card Game:** A simple "Is This My Card?" guessing game.

### How to Run the Program
1. **Unzip the file** to a location on your computer.
2. Open your terminal or command prompt and navigate to the unzipped folder.
3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

**Important:** Ensure the .env file is present in the root folder. This file contains the API keys and Database credentials required for the app to connect to the cloud database.

#### Run the application using Flask:

```
flask --app main.py --debug run
```
#### Open a web browser and go to: http://127.0.0.1:5000/

#### Future Work
Widget Management: Implement functionality to delete or remove widgets from the dashboard.
Drag-and-Drop: Allow users to rearrange the order of widgets on their dashboard.
