const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000; // Fondamentale per Railway

app.use(cors()); // Abilita CORS per permettere a n8n di connettersi

// Endpoint SSE
app.get('/events', (req, res) => {
    // 1. Imposta gli header necessari per SSE
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders(); // Invia subito gli header

    console.log('Client connesso');

    // 2. Invia dati a intervalli regolari
    const intervalId = setInterval(() => {
        const date = new Date().toLocaleTimeString();
        // Formato dell'evento SSE: "data: <messaggio>\n\n"
        res.write(`data: ${JSON.stringify({ timestamp: date, message: 'Questo è un evento dal server!' })}\n\n`);
    }, 1000);

    // 3. Gestisci la disconnessione del client
    req.on('close', () => {
        console.log('Client disconnesso');
        clearInterval(intervalId);
        res.end();
    });
});

app.get('/', (req, res) => {
    res.send('Server SSE è in esecuzione. Connettersi a /events per ricevere gli eventi.');
});

app.listen(PORT, () => {
    console.log(`Server in ascolto sulla porta ${PORT}`);
});