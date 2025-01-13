import { useState } from 'react';
import './App.css';

function Mybox({value, onSquareClick}) {

  return (
    <button className='Squarebox' onClick={onSquareClick}>{value}</button>
  ) 
}



function App() {
  const [xIsNext, setXIsNext] = useState(true);
  const [squares, setSquares] = useState(Array(9).fill(null));

  function handleClick(i) {
    if(calculateWinner(squares) || squares[i]) {
      return;
    }
    const nextbox = squares.slice();
    if(xIsNext) {
      nextbox[i] = "X";
    }
    else{
      nextbox[i] = "O";
    }
    setSquares(nextbox);
    setXIsNext(!xIsNext);
  }
  const winner = calculateWinner(squares);
  let status;
  if(winner) {
    status = "Winner: " + winner;
  } else{
    status = "Next player: "+ (xIsNext ? "X" : "O");
  }

  return (
    <>
    <div className='status'>{status}</div>
   <div className='ParentContainer'>

<div className="childcontainer">
  <Mybox value={squares[0]} onSquareClick={() => {handleClick(0)}}/>
  <Mybox value={squares[1]} onSquareClick={() => {handleClick(1)}}/>
  <Mybox value={squares[2]} onSquareClick={() => {handleClick(2)}}/>
</div>
<div className="childcontainer">
  <Mybox value={squares[3]} onSquareClick={() => {handleClick(3)}} />
  <Mybox value={squares[4]} onSquareClick={() => {handleClick(4)}}/>
  <Mybox value={squares[5]} onSquareClick={() => {handleClick(5)}}/>
</div>
<div className="childcontainer">
  <Mybox value={squares[6]} onSquareClick={() => {handleClick(6)}} />
  <Mybox value={squares[7]} onSquareClick={() => {handleClick(7)}}/>
  <Mybox value={squares[8]} onSquareClick={() => {handleClick(8)}}/>
</div>

   </div>
   </>
  );
}

function calculateWinner(squares) {
  const lines = [
    [0,1,2],
    [3,4,5],
    [6,7,8],
    [0,3,6],
    [1,4,7],
    [2,5,8],
    [0,4,8],
    [2,4,6],
  ];
  for (let i = 0; i <lines.length; i++) {
    const[a,b,c] = lines[i];
    if(squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
      return squares[a];
    }
  }
  return null;
}

export default App;
