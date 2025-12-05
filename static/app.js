let allTrackMetadata = [];
const audioPlayer = document.getElementById('audioPlayer');

let currentMixSequence = [];
let currentTrackIndex = 0;

async function fetchAllTracks() {
    try {
        const response = await fetch('/api/tracks');
        if (response.ok) {
            allTrackMetadata = await response.json();
            console.log(`Loaded ${allTrackMetadata.length} tracks into local lookup cache.`);
        }
    } catch (error) {
        console.error('Failed to load track metadata for playback lookup.', error);
    }
}

function getTrackDetailsById(id) {
    return allTrackMetadata.find(track => track.id === id);
}

function startSequentialPlayback(tracks) {
    const statusDiv = document.getElementById('mixStatus');

    currentMixSequence = tracks;
    currentTrackIndex = 0;

    audioPlayer.onended = () => {
        currentTrackIndex++;
        playNextTrackInSequence();
    };
    audioPlayer.onerror = (e) => {
        console.error("Audio error. Skipping:", e.target.error);
        currentTrackIndex++;
        playNextTrackInSequence();
    };

    playNextTrackInSequence();
}

function playNextTrackInSequence() {
    const statusDiv = document.getElementById('mixStatus');

    if (currentTrackIndex >= currentMixSequence.length) {
        statusDiv.innerText = 'Playlist finished.';
        audioPlayer.onended = null;
        audioPlayer.onerror = null;
        audioPlayer.src = '';
        return;
    }

    const track = currentMixSequence[currentTrackIndex];

    statusDiv.innerHTML =
        `Playing: <b>${track.title || track.name}</b> (${currentTrackIndex + 1} of ${currentMixSequence.length})`;

    // Extract the filename from the full path (handles both Windows '\' and Linux '/')
    const filename = track.file_path.split(/[/\\]/).pop();

    // Construct the URL using the static mount point "/tracks/"
    audioPlayer.src = `/tracks/${encodeURIComponent(filename)}`;

    audioPlayer.play().catch(e => {
        console.error("Autoplay prevented:", e);
        statusDiv.innerText = `Click Play! Browser blocked autoplay for track ${currentTrackIndex + 1}.`;
    });
}


async function uploadFiles() {
    const input = document.getElementById('musicFile');
    const uploadStatus = document.getElementById('uploadStatus');
    const files = input.files;
    const songGenre = document.getElementById('songGenre');

    if (songGenre.value.length === 0) {
        uploadStatus.innerText = "Genre cannot be empty";
        return;
    }

    uploadStatus.innerText = "Uploading...";

    for (const file of files) {
        const formdata = new FormData();
        formdata.append('file', file, file.name);
        formdata.append('genre', songGenre.value)

        try {
            const response = await fetch("/api/track/upload", {
                method: "POST",
                body: formdata
            })
            if (response.ok) {
                const result = await response.json();
                console.log("Upload Success:", result);
                uploadStatus.innerText = `Uploaded ${result.status}.`;
                await fetchAllTracks();
            } else {
                const errorText = await response.json();
                console.error("Upload Failed:", errorText);
                uploadStatus.innerText = ` Upload failed: ${errorText.detail || "Server Error"}`;
            }
        } catch (error) {
            console.error("Upload Network Error:", error);
            uploadStatus.innerText += ` Network error`;
        }
    }
}

async function generateMix() {
    const promptfield = document.getElementById('moodPrompt');
    const statusDiv = document.getElementById("mixStatus");
    const listContainer = document.getElementById('playlistTrackList');

    if (!promptfield.value) {
        statusDiv.innerText = "Prompt field is empty or undefined!";
        return;
    }
    if (allTrackMetadata.length === 0) {
        statusDiv.innerText = "Error: Please upload music tracks before generating a mix.";
        return;
    }

    const postData = { 'user_prompt': promptfield.value };
    statusDiv.innerText = "Generating mix with AI...";
    listContainer.innerHTML = '';

    try {
        const response = await fetch("/api/playlist/generate", {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(postData)
        });

        const data = await response.json();

        if (response.ok) {
            statusDiv.innerText = " Mix generated successfully!";

            const playlistResponse = data;

            const selectedTracks = playlistResponse.sort((a, b) => a.order - b.order);
            let sequencedTracks = [];

            selectedTracks.forEach(item => {
                const fullDetails = getTrackDetailsById(item.id);
                console.log(fullDetails);

                if (fullDetails) {
                    sequencedTracks.push({
                        ...fullDetails,
                        ...item
                    });

                    const pTag = document.createElement('p');
                    const title = item.name || fullDetails.title;
                    const artist = fullDetails.artist || 'Unknown Artist';
                    const weight = item.weight.toFixed(2);

                    pTag.textContent =
                        `#${item.order}: ${title} by ${artist} | Fit: ${weight}`;
                    pTag.className = 'playlist-track-entry';
                    listContainer.appendChild(pTag);
                } else {
                    const pTag = document.createElement('p');
                    pTag.textContent = `[Error] Track ID ${item.id} not found in library.`;
                    pTag.style.color = 'red';
                    listContainer.appendChild(pTag);
                }
            });

            if (sequencedTracks.length > 0) {
                // console.log(sequencedTracks);
                startSequentialPlayback(sequencedTracks);
            } else {
                statusDiv.innerText = "Error: AI returned an empty playlist or all selected IDs were invalid.";
            }

        } else {
            statusDiv.innerText = " Mix generation failed.";
            listContainer.innerHTML = `<p style="color: red;">Error: ${data.detail || "Server failed to generate mix."}</p>`;
            console.error("Backend Error:", data.detail || data);
        }
    }
    catch (error) {
        statusDiv.innerText = " Network error connecting to server.";
        console.error("Network error:", error);
    }
}

async function getTopTracks() {
    const topTracksList = document.getElementById('topTracksList');
    topTracksList.innerHTML = '<li>Fetching top tracks...</li>';

    try {
        const response = await fetch("/status/top-tracks");
        const result = await response.json();

        if (response.ok) {
            const trackList = result.data;
            topTracksList.innerHTML = '';

            if (Array.isArray(trackList)) {
                if (trackList.length === 0) {
                    topTracksList.innerHTML = '<li>No tracks have been used in mixes yet.</li>';
                    return;
                }
                trackList.forEach((track, index) => {
                    const listItem = document.createElement('li');
                    const title = track.title || track.name;
                    const count = track.mix_count || track.used || 0;

                    listItem.textContent = `#${index + 1}: ${title} (Used ${count} times)`;
                    topTracksList.appendChild(listItem);
                });
            } else {
                topTracksList.innerHTML = '<li>Error: Invalid track list format from cache.</li>';
            }
        } else {
            const errorData = result.detail ? result : { detail: response.statusText };
            topTracksList.innerHTML = `<li>Error: ${errorData.detail || "Server could not fetch top tracks."}</li>`;
        }
    }
    catch (error) {
        console.error(`Error fetching top tracks: ${error}`);
        topTracksList.innerHTML = `<li>Network or fetching error.</li>`;
    }
}

fetchAllTracks();