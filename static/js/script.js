document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("network");
    const outputContent = document.getElementById("output-content");

    let network, nodes, edges; // Global değişkenler

    // Ekran boyutu değiştiğinde grafiği otomatik boyutlandırmak için fonksiyon
    function resizeNetwork(network) {
        window.addEventListener("resize", () => {
            network.setSize("100%", "100%");
            network.redraw();
        });
    }

    // Flask'teki "/get_graph_data" endpoint'inden grafik verisini çekme
    function fetchGraphData() {
        return fetch("/get_graph_data")
            .then(response => {
                if (!response.ok) throw new Error("Veri çekilemedi! HTTP Hatası: " + response.status);
                return response.json();
            });
    }

    // Grafiği oluşturma fonksiyonu
    function createNetwork(graphData) {
        nodes = new vis.DataSet(graphData.nodes);
        edges = new vis.DataSet(graphData.edges);

        const data = { nodes: nodes, edges: edges };
        const options = {
            nodes: {
                shape: "dot",
                font: { size: 14, color: "#333" },
                borderWidth: 2,
                scaling: { min: 10, max: 30 }
            },
            edges: {
                width: 2,
                color: { color: "#848484", highlight: "#3c3c3c" }
            },
            interaction: { hover: true, tooltipDelay: 200 },
            physics: {
                enabled: true,
                solver: "forceAtlas2Based",
                stabilization: { iterations: 100 }
            },
            layout: { improvedLayout: true }
        };

        network = new vis.Network(container, data, options);
        resizeNetwork(network);

        // Düğüm üzerine tıklandığında bilgi göster
        network.on("selectNode", function (params) {
            const nodeId = params.nodes[0];
            const node = graphData.nodes.find(n => n.id === nodeId);
            if (node) {
                outputContent.innerHTML = `<b>Seçilen Yazar:</b> ${node.label}<br><b>Toplam Makale:</b> ${node.title}`;
            }
        });
    }

    // Sunucudan veri al ve grafiği güncelle
    function processRequest(action) {
        const authorA = document.getElementById("author_a")?.value || "";
        const authorB = document.getElementById("author_b")?.value || "";

        fetch('/process_request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action, author_a: authorA, author_b: authorB })
        })
        .then(response => response.json())
        .then(data => {
            // Çıktı ekranını güncelle
            outputContent.innerHTML = data.status === 'success'
                ? `<b>${data.result}</b>`
                : `<b style="color:red;">Hata:</b> ${data.result}`;

            // Eğer vurgulanacak düğüm varsa
            if (data.highlight_nodes) {
                highlightNodesWithAnimation(data.highlight_nodes);
            }
        })
        .catch(error => {
            console.error('Hata:', error);
            outputContent.innerHTML = `<pre style="color:red;">Sunucu hatası!</pre>`;
        });
    }

    // Belirtilen düğümleri kırmızıya çevirip 2 saniye sonra eski haline döndüren fonksiyon
    function highlightNodesWithAnimation(highlightNodes) {
        // Düğümleri kırmızıya çevir
        highlightNodes.forEach(nodeId => {
            nodes.update({ id: nodeId, color: { background: 'red', border: 'darkred' } });
        });

        // 2 saniye sonra düğümleri eski haline getir
        setTimeout(() => {
            highlightNodes.forEach(nodeId => {
                nodes.update({ id: nodeId, color: { background: 'blue', border: 'darkblue' } });
            });
        }, 2000);
    }

    // Sayfa yüklendiğinde yapılacak işlemler
    fetchGraphData()
        .then(graphData => {
            createNetwork(graphData); // Grafiği oluştur
            setupButtons(); // Butonları aktif hale getir
        })
        .catch(error => {
            console.error("Grafik verisi yüklenirken hata oluştu:", error);
            alert("Grafik verisi yüklenirken bir hata oluştu. Lütfen tekrar deneyin.");
        });

    // Butonlara olay dinleyicisi ekleme
    function setupButtons() {
        document.querySelectorAll("button").forEach(button => {
            button.addEventListener("click", () => {
                const action = button.getAttribute("data-action");
                processRequest(action);
            });
        });
    }
});
