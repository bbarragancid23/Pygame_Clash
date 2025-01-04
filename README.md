# Pygame_Clash  
A minimalistic remake of the building and attacking mechanics from the mobile game *Clash of Clans*, built using the Python library **Pygame**.

## Features  
- **Game Modes**: Switch seamlessly between **Build Mode** and **Attack Mode**.  
- **Zoom and Map Navigation**:  
  - Zoom in/out centered on the cursor ([Pinch Zoom] or [LCTRL + MOUSEWHEEL]).  
  - Navigate the map ([MOUSEWHEEL]).  
- **Buildings and Troops**: Includes 6 buildings and 6 troops inspired by the original game, each with properties similar to the original.  
- **AI Pathfinding**: Troops use a modified **A* Search Algorithm** for dynamic and intelligent pathfinding.  

## Controls  
- **[Tab]**: Toggle between Build Mode and Attack Mode.  
- **[Esc]**: Exit the game.  
- **[Pinch Zoom] / [LCTRL + MOUSEWHEEL]**: Zoom in/out.  
- **[MOUSEWHEEL]**: Scroll the map horizontally or vertically.  

## Gameplay  
### Build Mode  
- Drag and drop any of the six buildings from the toolbar at the bottom of the screen.  
- Buildings snap to the grid, even if the mouse is slightly off-grid.  
- Placement restrictions:  
  - Cannot place buildings outside the grid.  
  - Prevents overlapping buildings.  
- Inventory limits for each building type.

### Attack Mode  
- Select a troop by clicking it (indicated by a darker tint).  
- Place troops anywhere on the map, including the dark green border areas.  
- Troop behaviors:  
  - **Barbarians (0)** and **Archers (1)**: Target any building.  
  - **Giants (2)** and **Balloons (5)**: Prioritize defensive buildings, then target others.  
  - **Goblins (3)**: Target resource buildings first, then others.  
  - **Wall Breakers (4)**: Target the nearest wall adjacent to a building.  

## Data and Customization  
- All building and troop properties are defined in CSV files located in the `data` directory.  
- Modify the CSV files to adjust properties such as health, damage, and behaviors.  

## Installation and Running the Game  
1. Clone the repository:  
   ```bash
   git clone https://github.com/<your-username>/Pygame_Clash.git
   cd Pygame_Clash
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
3. Enjoy!:
   ```bash
   python main.py

## Acknowledgments
This project was inspired by Clash of Clans and aims to replicate its core building and attacking mechanics in a simplified form.
