function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    const chatBox = document.getElementById('chat-box');
    const errorMessage = document.getElementById('error-message');

    // エラーメッセージを非表示に
    errorMessage.style.display = 'none';

    // チャットボックスにユーザーのメッセージを表示
    chatBox.innerHTML += `<div class="message"><strong>You:</strong> ${userInput}</div>`;
    
    // GPT-3.5にメッセージを送信
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        // GPT-3.5からの応答をチャットボックスに表示
        chatBox.innerHTML += `<div class="message"><strong>GPT-3.5:</strong> ${data.response}</div>`;
        
        // 入力欄をクリア
        document.getElementById('user-input').value = '';

        // YouTube APIから関連動画を取得
        fetch(`/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: userInput }), // userInputが正しく設定されているか確認
        })

        .then(response => response.json())
        .then(data => {
            // 動画結果の表示エリアを取得
            const videoResults = document.getElementById('video-results');
            videoResults.innerHTML = '';  // 過去の結果をクリア

            // 各動画結果をHTMLに追加
            if (data.videos && data.videos.length > 0) {
                data.videos.forEach(video => {
                    const videoElement = `
                        <div class="video-item">
                            <a href="https://www.youtube.com/watch?v=${video.videoId}" target="_blank">
                                <img src="${video.thumbnail}" alt="サムネイル">
                                <h3>${video.title}</h3>
                                <p>${video.description}</p>
                            </a>
                        </div>
                    `;
                    videoResults.innerHTML += videoElement;
                });
            } else {
                videoResults.innerHTML = `<p>No videos found.</p>`;
            }
        })
        .catch(error => {
            errorMessage.innerHTML = `Error fetching videos: ${error}`;
            errorMessage.style.display = 'block'; // エラーメッセージを表示
        });
    })
    .catch(error => {
        errorMessage.innerHTML = `Error: ${error}`;
        errorMessage.style.display = 'block'; // エラーメッセージを表示
    });
}

// 自由検索処理を行う関数
function performCustomSearch() {
    const customSearchInput = document.getElementById('custom-search-input').value;
    const customSearchResults = document.getElementById('custom-search-results');
    const errorMessage = document.getElementById('error-message');

    // エラーメッセージを非表示に
    errorMessage.style.display = 'none';
    customSearchResults.innerHTML = ''; // 過去の結果をクリア

    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: customSearchInput }), // 検索クエリをサーバーに送信
    })
    .then(response => response.json())
    .then(data => {
        if (data.videos && data.videos.length > 0) {
            data.videos.forEach(video => {
                const videoElement = `
                    <div class="video-item">
                        <a href="https://www.youtube.com/watch?v=${video.videoId}" target="_blank">
                            <img src="${video.thumbnail}" alt="サムネイル">
                            <h3>${video.title}</h3>
                            <p>${video.description}</p>
                        </a>
                    </div>
                `;
                customSearchResults.innerHTML += videoElement;
            });
        } else {
            customSearchResults.innerHTML = `<p>該当する動画が見つかりませんでした。</p>`;
        }
    })
    .catch(error => {
        errorMessage.innerHTML = `Error fetching videos: ${error}`;
        errorMessage.style.display = 'block';
    });
}

function Greeting() {
    var nt = new Date();
    var hr = nt.getHours();
    var greetingText = ""; // 挨拶メッセージを格納

    if (hr <= 1) { greetingText = '夜はこれから！'; }
    else if (hr <= 3) { greetingText = 'そろそろ寝た方がいいんじゃ…？'; }
    else if (hr <= 5) { greetingText = '早いですね。もしくは徹夜？'; }
    else if (hr <= 7) { greetingText = 'おはようございます。'; }
    else if (hr <= 9) { greetingText = 'そろそろお仕事ですか？'; }
    else if (hr <= 11) { greetingText = 'こんにちは。'; }
    else if (hr <= 13) { greetingText = 'お昼時です。お腹空きませんか？'; }
    else if (hr <= 15) { greetingText = 'おやつの時間です。'; }
    else if (hr <= 17) { greetingText = 'そろそろ夕方ですね。'; }
    else if (hr <= 19) { greetingText = 'そろそろ夕食ですか？'; }
    else if (hr <= 21) { greetingText = 'こんばんは。'; }
    else if (hr <= 23) { greetingText = 'ネットが混み出す頃ですね。'; }

    // 指定されたHTML要素にメッセージを挿入
    var greetingElement = document.getElementById("greeting");
    if (greetingElement) {
        greetingElement.textContent = greetingText;
    }
}

// コメント投稿（POST）
document.getElementById('comment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const comment = document.getElementById('comment').value;

    try {
        const response = await fetch('/comments', {
            method: 'POST', // POSTメソッド
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, comment })
        });

        if (response.ok) {
            console.log("コメントが追加されました");
            loadComments(); // コメントリストをリロード
        } else {
            console.error("エラー: コメント送信に失敗しました");
        }
    } catch (error) {
        console.error("Error posting comment:", error);
    }
});

// コメント取得処理 (GET)
async function loadComments() {
    try {
        const response = await fetch('/comments');
        const comments = await response.json();
        renderComments(comments);
    } catch (error) {
        showError("コメントの取得中にエラーが発生しました: " + error.message);
    }
}

function renderComments(comments) {
    const section = document.getElementById('comment-section');
    section.innerHTML = '<h2>コメント一覧</h2>';
    comments.forEach(comment => {
        section.innerHTML += `
            <div class="comment">
                <strong>${comment.username}</strong>
                <p>${comment.content}</p>
                <span class="comment-time">${comment.created_at}</span>
            </div>
        `;
    });
}

async function postComment() {
    const username = document.getElementById('username').value;
    const comment = document.getElementById('comment').value;

    try {
        const response = await fetch('/comments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, comment })
        });

        if (response.ok) {
            loadComments();
            document.getElementById('comment-form').reset();
        } else {
            showError("コメントの送信に失敗しました。");
        }
    } catch (error) {
        showError("Error posting comment: " + error.message);
    }
}

// イベントリスナー
document.getElementById('comment-form').addEventListener('submit', (e) => {
    e.preventDefault();
    postComment();
});

// 初期読み込み
loadComments();

