// id="keywords" を取得
const keywords = document.getElementById('keywords');

// キーワード入力を監視
keywords.addEventListener('keypress', (event) => {
    // フォームに何か入っている状態で、カンマもしくはエンターが押された
    if (event.target.value && (event.key === ',' || event.key === 'Enter')) {
        // キーワードHTMLの枠を作成
        const div = document.createElement('div');
        div.setAttribute('class', 'keyword');
        div.textContent = event.target.value;
        // ボタンを作成
        const button = document.createElement('button');
        button.setAttribute('type', 'button');
        button.setAttribute('class', 'delete-keyword');
        // x アイコン
        button.innerHTML = '<i class="bi bi-x-circle"></i>';
        // x ボタンを押されたら自害
        button.addEventListener('click', (event) => {
            event.target.closest('button').parentElement.remove();
        });
        div.appendChild(button);

        const fixKeywords = document.getElementById('fix-keywords');
        fixKeywords.appendChild(div);

        // 入力をクリア
        event.target.value = '';
    }

    // カンマとエンターを押しても何もしないように制御
    // これをしないとカンマが残ったり、次のフォームに移ったりする
    if (event.key === ',' || event.key === 'Enter') {
        event.preventDefault();
    }
});