document.addEventListener("DOMContentLoaded", function () {
    // Görselleştirme alanı için HTML'deki "network" id'sini seçiyoruz
    var container = document.getElementById("network");

    // Ekran boyutu değiştiğinde grafiği otomatik boyutlandırmak için fonksiyon
    function resizeNetwork(network) {
        window.addEventListener("resize", () => {
            network.setSize("100%", "100%");
            network.redraw();
        });
    }

    // Flask'teki "/get_graph_data" endpoint'inden veri çekiyoruz
    fetch("/get_graph_data")
        .then(response => {
            if (!response.ok) {
                throw new Error("Veri çekilemedi! HTTP Hatası: " + response.status);
            }
            return response.json(); // JSON formatına çevir
        })
        .then(graphData => {
            console.log("Gelen Grafik Verisi:", graphData); // Kontrol için konsola yaz

            // Gelen veriyi Vis.js için uygun hale getir
            var nodes = new vis.DataSet(graphData.nodes); // Düğümler
            var edges = new vis.DataSet(graphData.edges); // Kenarlar

            // Veriyi Vis.js için birleştir
            var data = {
                nodes: nodes,
                edges: edges
            };

            // Grafik ayarları
            var options = {
                nodes: {
                    shape: "dot", // Düğüm şekli
                    font: {
                        size: 14,   // Düğüm üzerindeki yazı boyutu
                        color: "#333" // Yazı rengi
                    },
                    borderWidth: 2, // Düğüm kenar kalınlığı
                    scaling: {
                        min: 10, // Minimum boyut
                        max: 30  // Maksimum boyut
                    }
                },
                edges: {
                    width: 2, // Kenar kalınlığı
                    color: {
                        color: "#848484", // Normal kenar rengi
                        highlight: "#3c3c3c" // Kenar üzerine gelindiğinde renk
                    }
                },
                interaction: {
                    hover: true, // Üzerine gelince hover efekti
                    tooltipDelay: 200 // Tooltip gecikmesi
                },
                physics: {
                    enabled: true, // Fizik motoru aktif (düğümler otomatik yayılır)
                    solver: "forceAtlas2Based", // Fizik algoritması
                    stabilization: {
                        iterations: 100 // Stabilizasyon adımı artırıldı
                    }
                },
                layout: {
                    improvedLayout: true // Daha iyi düzen sağlamak için
                }
            };

            // Grafiği oluştur
            var network = new vis.Network(container, data, options);

            // Grafiği otomatik boyutlandır
            resizeNetwork(network);

            // Düğüm üzerine tıklandığında bilgi göster
            network.on("selectNode", function (params) {
                var nodeId = params.nodes[0]; // Tıklanan düğümün ID'si
                var node = graphData.nodes.find(n => n.id === nodeId); // Düğüm bilgisi
                if (node) {
                    alert(`Seçilen Yazar: ${node.label}\nToplam Makale: ${node.title}`);
                }
            });
        })
        .catch(error => {
            console.error("Grafik verisi yüklenirken hata oluştu:", error);
            alert("Grafik verisi yüklenirken bir hata oluştu. Lütfen tekrar deneyin.");
        });
});
