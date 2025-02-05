(function() {
    const boardElement = document.getElementById('board');
    const size = 3;
    let board = Array.from({ length: size }, () => Array(size).fill(''));
    let currentPlayer = 'X';
    let gameOver = false;

    function renderBoard() {
        boardElement.innerHTML = '';
        for (let i = 0; i < size; i++) {
            for (let j = 0; j < size; j++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.row = i;
                cell.dataset.col = j;
                cell.textContent = board[i][j];
                cell.addEventListener('click', onCellClick);
                boardElement.appendChild(cell);
            }
        }
    }

    function onCellClick(e) {
        if (gameOver) return;
        const row = parseInt(e.target.dataset.row);
        const col = parseInt(e.target.dataset.col);
        if (board[row][col] !== '') return;

        board[row][col] = currentPlayer;
        if (checkWinner(currentPlayer)) {
            alert(currentPlayer + ' wins!');
            gameOver = true;
        } else if (isBoardFull()) {
            alert("It's a draw!");
            gameOver = true;
        } else {
            currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
        }
        renderBoard();
    }

    function isBoardFull() {
        for (let i = 0; i < size; i++) {
            for (let j = 0; j < size; j++) {
                if (board[i][j] === '') return false;
            }
        }
        return true;
    }

    function checkWinner(player) {
        // Check rows
        for (let i = 0; i < size; i++) {
            if (board[i].every(cell => cell === player)) return true;
        }
        // Check columns
        for (let j = 0; j < size; j++) {
            let colWin = true;
            for (let i = 0; i < size; i++) {
                if (board[i][j] !== player) {
                    colWin = false;
                    break;
                }
            }
            if (colWin) return true;
        }
        // Check diagonals
        let diag1 = true, diag2 = true;
        for (let i = 0; i < size; i++) {
            if (board[i][i] !== player) diag1 = false;
            if (board[i][size - 1 - i] !== player) diag2 = false;
        }
        return diag1 || diag2;
    }

    // Optional: load DSL config for game customization
    // For now, we rely on the hardcoded defaults.

    renderBoard();
})();
