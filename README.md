# KFX CK8 PRO Advanced Remote Script for Ableton Live

## Overview

This repository is a **Fork** based on the original work by the creators of [MIDIMixD / MIDI Mix remote script for Ableton Live](https://github.com/diff-arch/MIDIMixD).

This script is specifically designed for the **KFX CK8 PRO** MIDI controller, which shares the physical layout of the **Akai MIDI Mix**, but features crucial hardware behavior differences.

### Why this Fork was created (KFX CK8 PRO Adaptations)
On the original Akai MIDI Mix, features like `SOLO` buttons are used for modifier combinations (such as `SOLO + BANK RIGHT`). However, on the **KFX CK8 PRO** controller, the `SOLO` button does not send standard MIDI CC or note messages in the same way for modifier combinations. 

To make this controller fully functional in Ableton Live, this script adapts the control architecture:
- **Shift Function:** Moved from `SOLO` to **`REC ARM 1`** (holding down the first track's `REC ARM` button acts as `Shift`).
- **Mode Switching & Navigation:** Adapted specifically for the CK8 PRO layout and workflow.

---

## Detailed Features & Workflow

The script operates in two main modes, giving you both traditional mixing control and advanced device parameter editing.

### 1. Mode 1: Mixer Mode (Traditional Mixing)
Designed for standard mixing tasks across 8 tracks at a time:
- **Knobs (Rows 1, 2, and 3):** Control **Sends A, B, and C** for each channel.
- **Shift + Knobs (Rows 1, 2, and 3):** Hold `REC ARM 1` (`Shift`) while turning knobs to control **Sends D, E, and Track Panning**.
- **Faders 1–8:** Control track **Volume** (top position corresponds to 0 dB).
- **BANK L / R:** Shifts the 8-track bank left or right across your session.

### 2. Mode 2: Device & Parameter Mode (Deep Device Control)
Designed for tweaking plugin and device parameters directly from your hardware:
- **Knobs (Rows 1, 2, and 3):** Control the **first 8 parameters** of the selected device across tracks 1, 2, and 3.
- **Faders 1–8:** **Select devices** on each track. Moving a fader from bottom to top cycles through and selects the devices loaded on that track.
- **BANK L / R:** Shifts by 3 tracks.

### 3. Mode Switching Shortcuts
- **Switch to Mode 2:** Hold `Shift` (`REC ARM 1`) + press **`BANK RIGHT`**.
- **Return to Mode 1:** Hold `Shift` (`REC ARM 1`) + press **`BANK LEFT`**.

### 4. REC ARM Multi-Functionality (Tap & Select)
The `REC ARM` buttons on channels 1 through 8 double as track selection and arming buttons:
- **Single Short Tap:** Arms or disarms the track for recording.
- **Double Tap (Two quick taps):** Selects the track in Ableton Live.

### 5. Parameter Pickup (No Jumps)
Both knobs and faders feature **Pickup** (`PICKUP_KNOBS = True`, `PICKUP_FADERS = True`). When switching modes or pages, a control will not affect the software parameter until your physical knob/fader position crosses or matches the current software value, preventing sudden audio jumps.

### 6. Send All Button
Pressing the **`SEND ALL`** button (or when rapid control changes occur) instantly forces all physical knob positions to be sent to their current targets, ignoring pickup temporarily so your parameters instantly sync with the hardware knobs.

### 7. Session Box & LED Feedback
- **Red Session Box:** Automatically draws and keeps the session highlight box aligned in Ableton Live.
- **LED Feedback:** Real-time feedback lights up the hardware LED buttons for Mute and Arm states.

---

## Installation (Beginner-Friendly Guide)

If you are not familiar with Git or command-line tools, you can easily install this script by downloading a ZIP file:

### Step 1: Download the ZIP File
1. Scroll to the top of this GitHub repository page.
2. Click the green **`<> Code`** button.
3. Click **`Download ZIP`**.
4. Save the file to your computer and extract (unzip) it. You will get a folder containing the script files.

### Step 2: Locate your Ableton Live "Remote Scripts" Folder
1. Open **Ableton Live**.
2. Go to **Preferences** (or **Settings** on newer versions) -> **File / Folder**.
3. Locate your **User Library** path.
4. Open your `User Library` folder on your computer's file explorer (Finder on macOS, File Explorer on Windows).
5. Inside your `User Library`, check if there is a folder named **`Remote Scripts`**. If it does not exist, create a new folder and name it exactly `Remote Scripts`.

### Step 3: Install the Script
1. Move or copy the extracted script folder inside your `Remote Scripts` folder and name it to **`kfx_ck8_pro`**:

   `User Library/Remote Scripts/kfx_ck8_pro/`
   > ⚠️ **Important Python Note:** Make sure the folder name **does not contain spaces or hyphens** (e.g., use `kfx_ck8_pro` instead of `Kfx Ck8 pro`). Python package naming rules require valid module identifiers; otherwise, Ableton Live's Python interpreter will fail to load the script.

### Step 4: Enable in Ableton Live
1. Restart Ableton Live.
2. Open **Preferences** -> **Link / Tempo / MIDI**.
3. Under the **Control Surface** dropdown, select **MIDI Mix** (or the script name).
4. Set both **Input** and **Output** ports to your KFX CK8 PRO controller.

---

## Contributions & Discussion

We welcome contributions, bug reports, and feature discussions! If you want to help improve this script:

1. **Open an Issue:** If you encounter a bug, have questions, or want to suggest an enhancement, please open an Issue detailing your Ableton Live version and steps to reproduce.
2. **Submit a Pull Request (PR):**
   - Fork the repository.
   - Create a feature branch (`git checkout -b feature/AmazingFeature`).
   - Commit your changes with clear messages (`git commit -m 'Add some AmazingFeature'`).
   - Push to your branch (`git push origin feature/AmazingFeature`).
   - Open a Pull Request against the main branch.
3. **Good Practices:**
   - Keep code clean, readable, and structured.
   - Document any new controller mappings or behavior updates.
   - Discuss major architectural changes in an Issue before starting implementation.

---

## Credits & License

- **Original Project:** Forked from [MIDIMixD by diff-arch](https://github.com/diff-arch/MIDIMixD).
- **License:** Distributed under the MIT License. See `LICENSE.txt` for more information.
