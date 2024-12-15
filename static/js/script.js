document.addEventListener("DOMContentLoaded", function () {
    // Grafiği görselleştirme için gerekli DOM elementi
    var container = document.getElementById("network");

    // Sunucudan JSON veri çekme işlemi
    fetch("/get_graph_data")  // Doğrudan Flask endpoint'i çağır
        .then(response => {
            if (!response.ok) {
                throw new Error("Veri çekilemedi! HTTP Hatası: " + response.status);
            }
            return response.json();
        })
        .then(graphData => {
            console.log("Gelen Grafik Verisi:", graphData); // Konsolda kontrol

            // Vis.js için düğümler ve kenarlar
            var nodes = new vis.DataSet(graphData.nodes);
            var edges = new vis.DataSet(graphData.edges);

            var data = {
                nodes: nodes,
                edges: edges
            };

            // Grafiği oluşturmak için seçenekler
            var options = {
                nodes: {
                    shape: "dot",
                    size: 20,
                    font: {
                        size: 14,
                        color: "#333",
                    },
                    borderWidth: 2
                },
                edges: {
                    width: 2,
                    color: {
                        color: "#848484",
                        highlight: "#3c3c3c",
                    },
                    arrows: {
                        to: { enabled: false }
                    }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200
                },
                physics: {
                    enabled: true,
                    solver: "forceAtlas2Based",
                    stabilization: {
                        iterations: 50
                    }
                }
            };

            // Grafiği oluştur
            var network = new vis.Network(container, data, options);

            // Düğüm üzerine tıklandığında gösterilecek bilgi
            network.on("selectNode", function (params) {
                var nodeId = params.nodes[0];
                var node = graphData.nodes.find(n => n.id === nodeId);
                if (node) {
                    alert(`Seçilen Yazar: ${node.label}\nMakaleler: ${node.title}`);
                }
            });
        })
        .catch(error => {
            console.error("Grafik verisi yüklenirken hata oluştu:", error);
        });
});
