"""
About page for the Shadow Reloaded dashboard.

This script defines the "Game & Dashboard Info" page displayed in the Streamlit app.
It uses embedded HTML and base64-encoded images to ensure the page
is self-contained (no external file dependencies), and also injects CSS for styling.
"""
import streamlit as st

from constants import ABOUT_PAGE_FAVICON, ABOUT_PAGE_CSS, STAGE_CHART_PNG, SG_SHOWCASE_GIF
from dashboard_core.utils import load_image_as_base64
from dashboard_core.ui.ui_utils import nav_bar

nav_bar()

st.set_page_config(
    page_title="Game & Dashboard Info",
    page_icon=ABOUT_PAGE_FAVICON,
    layout="wide",
)

# Apply CSS specific to this page
st.html(ABOUT_PAGE_CSS)

# Convert image files to base64 data URIs for inline embedding
png_uri = load_image_as_base64(STAGE_CHART_PNG)
gif_uri = load_image_as_base64(SG_SHOWCASE_GIF)

# Render the 'Game & Dashboard Info' page content as raw HTML inside Streamlit
# (self-contained with embedded CSS and images)
st.html(
f"""
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description"
        content="Shadow Reloaded: Game Overview, Categories, Characters, SG glitch, and Dashboard Usage.">
    <title>Game & Dashboard Info</title>
</head>

<body>
    <div id="about-page">
        <header>
            <h1>Game & Dashboard Info</h1>
            <hr>
            <nav>
                <ul>
                    <li><a href="#game-info">Game Overview</a></li>
                    <li><a href="#level-fullgame-structure">Level and Full Game Category Structure</a></li>
                    <li><a href="#characters">Characters</a></li>
                    <li><a href="#sg-glitch">SG (Spindash/Slide Glide) Explained</a></li>
                    <li><a href="#dashboard-info">About this Dashboard</a></li>
                </ul>
            </nav>
            <hr>
        </header>

        <main>
            <section id="game-info">
                <h2>Game Overview</h2>
                <p>
                    <a href="https://github.com/ShadowTheHedgehogHacking/ShdTH-Reloaded" target="_blank"
                        rel="noopener noreferrer">Shadow Reloaded</a> is a gameplay overhaul ROM hack of
                    <strong>Shadow the Hedgehog (2005)</strong> designed to make the game more fluid and less tedious.
                    It increases the challenge with remixed <strong>Expert Mode</strong> levels (and <b>Shadow Box</b>
                    removed), new Rank S, restores unused content and makes <strong>Androids</strong> playable
                    outside 2-Player Mode.
                    <br>
                    It features improved movement such as faster <b>Homing Attacks</b>, precise <b>Slide</b> control,
                     consistent <b>Light Dashes</b> and a
                    dedicated button to guarantee a <b>Jump Dash</b>.
                    <abbr title="Quality of Life">QoL</abbr> improvements include accurate in-game timing for speedruns
                    and
                    the ability to select
                    <strong>Expert</strong> level variants in <b>Select Mode</b> using the X button.
                </p>
            </section>

            <section id="level-fullgame-structure">
                <h2>Level and Full Game Category Structure</h2>
                <p><strong>Levels</strong> can include up to four mission categories: <strong>Dark, Normal,
                        Hero,</strong>
                    and <strong>Expert</strong>,
                    depending on their position in the stage chart shown above.
                </p>

                <ul>
                    <li><b>Core Levels:</b> Contain all four categories - <b>Dark / Normal / Hero / Expert</b>.</li>
                    <li><b>Outer Levels:</b> Contain three categories - <b>Dark or Hero / Normal / Expert</b>.</li>
                    <li><b>Final Stages:</b> Contain three categories - <b>Dark / Hero / Expert</b>.</li>
                </ul>

                <p>
                    <b>Expert Missions</b> exist for every stage, but are normally only accessible in <b>Expert Mode</b>
                    or
                    by selecting the stage with the X button in <b>Select Mode</b>.<br>
                    <b>The Last Way</b> is the only level with only 2 missions: <b>Normal</b> and
                    <b>Expert</b>.<br>
                    <strong>Bosses</strong> feature only <b>Normal</b> and <b>Expert</b> missions (with Expert typically
                    only
                    available via Select Mode with X button), expect <b>Devil Doom</b>, which only has a <b>Normal</b>
                    mission.
                </p>

                <p>
                    <strong>Full Game</strong> is a separate scope with its own categories, each requiring the player to
                    follow a
                    specific route through the stage chart.<br>
                    <b>Expert Mode</b> is a distinct gameplay mode in which the player must complete every stage on
                    <b>Expert</b> difficulty in a single run.
                </p>                
                
                <figure>
                    <img src="{png_uri}" alt="Stage and Boss Chart">
                    <figcaption>Chart of the levels in Shadow the Hedgehog</figcaption>
                </figure>
            </section>

            <section id="characters">
                <h2>Characters</h2>
                <p>There are three playable character types, each with distinct weapon capabilities and speedrun
                    implications:
                </p>

                <ul>
                    <li>
                        <strong>Shadow</strong> - The default character. He can pick up and use any weapon found in the
                        stage, offering the most versatility.
                    </li>
                    <li>
                        <strong>Gun Android</strong> - Equipped with a built-in <strong>semi-automatic rifle with
                            unlimited
                            ammo</strong> (4 damage per shot, rapid fire). Generally considered the fastest and easiest
                        character to speedrun with due to <b>reliable damage</b> and no need to pick up weapons.
                    </li>
                    <li>
                        <strong>Cannon Android</strong> - Uses an arm-mounted <strong>cannon with unlimited
                            ammo</strong>
                        (8 damage per shot, slower rate of fire). Difficult to use effectively due to <b>lack of
                            auto-aim</b> and lower consistency in hitting targets, often resulting in slower run times.
                    </li>
                </ul>

                <p>
                    Since <b>Androids</b> cannot pick up weapons, certain level and category combinations are not
                    completable with them. However, their built-in weapons also bypass many of the intended gimmicks in
                    <b>Expert Boss</b> fights, making most of them significantly easier.
                </p>
            </section>

            <section id="sg-glitch">
                <h2>SG (Spindash/Slide Glide) Explained</h2>
                <p>
                    <strong><abbr title="Spindash / Slide Glide">SG</abbr></strong> is a <b>glitch</b> unique to
                    <strong>Shadow Reloaded</strong> that allows the player to perform <strong>mid-air
                        Spindashes</strong>. To execute it, you must first be holding the <b>Slide</b> button in
                    mid-air.
                    Then, release <b>Slide</b> and - exactly <strong>three frames</strong> later - press the
                    <b>Spindash</b>
                    button. Pressing it later will cause the trick to fail.
                </p>

                <p>
                    Although <b>SG</b> may sound extremely powerful, it is primarily useful for skipping specific
                    sections in certain levels. The most notable case is in <b>Lost Impact Normal/Expert</b>,
                    where it allows you to skip the entire stage. However, because it is frame-perfect and
                    charging a <b>Spindash</b> in mid-air is often slower than simply running, its practical use is
                    mostly
                    limited to targeted skips.
                </p>

                <figure>
                    <img src="{gif_uri}" alt="SG Showcase">
                    <figcaption>Lost Impact Normal skip using SG.</figcaption>
                </figure>

                <p>
                    The dashboard includes run data with and without <b>SG</b> usage, allowing comparisons between
                    traditional and glitch-optimized strategies.
                </p>
            </section>

            <section id="dashboard-info">
                <h2>About this Dashboard</h2>
                <p>
                    This dashboard visualises community-submitted runs for <b>Shadow Reloaded</b>.
                    Data is fetched from <strong>Speedrun.com</strong> and supplemented with local cache files stored
                    under the project's
                    <code>data/cache/</code> directory. Use the <strong>Refresh Data</strong> button in the app to fetch
                    fresh data (a cooldown is applied to avoid excessive requests).
                </p>

                <p>Key features:</p>
                <ul>
                    <li><strong>Table View:</strong> Displays recorded runs and ranks with optional inclusion of
                        <b>obsolete</b> entries.
                    </li>
                    <li>
                        <strong>Charts:</strong> Multiple visualisations including <strong>PB Progression</strong>
                        (personal-best lines),
                        <strong>Player Time Improvements</strong> (per-run markers and total-improvement bars),
                        <strong>Current WR Counts</strong>, and a <strong>Community Overview</strong> with activity over
                        time and aggregated community metrics.
                    </li>
                    <li>
                        <strong>Interactivity:</strong> Hover to see formatted times, run date and note. Click legend
                        entries to filter players, use drag/zoom to inspect ranges, and (for <b>PB Progression</b>) select a
                        player to compare their times across all three <b>characters</b>.
                    </li>
                </ul>

            </section>
        </main>
    </div>
</body>

</html>
"""
)
