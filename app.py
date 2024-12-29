from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import sys
import re  # Regex kullanarak isimleri normalize etmek için

app = Flask(__name__)

EXCEL_FILE_PATH = r"C:\Users\Acer\PycharmProjects\PROLAB_3\PROLAB 3 - GUNCEL DATASET.xlsx"

def clean_name(name):
    name = re.sub(r'\s+', ' ', name.strip())  # Çift boşlukları tek boşluk yapar
    name = re.sub(r"[^\w\s]", '', name)  # Özel karakterleri kaldırır (sadece harf ve boşluk bırakır)
    return name.lower()  # Küçük harf

def create_graph(file_path):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        raise ValueError(f"Excel dosyası okunamadı: {e}")

    G = {}  # Ana graf yapısı
    author_papers = {}  # Yazarların makale listelerini tutar

    for _, row in df.iterrows():
        # Ana yazar ismini temizle ve normalize et
        main_author = clean_name(str(row['author_name']))

        # Ortak yazarları temizle ve normalize et
        coauthors = [
            clean_name(coauthor)
            for coauthor in str(row['coauthors']).split(",")
            if clean_name(coauthor) and clean_name(coauthor) != main_author
        ]

        paper_title = str(row['paper_title']).strip()

        # Ana yazarın makale listesini güncelle
        if main_author not in author_papers:
            author_papers[main_author] = []
        author_papers[main_author].append(paper_title)

        # Ana yazarı graf yapısına ekle
        if main_author not in G:
            G[main_author] = {}

        # Ortak yazarları ekle
        for coauthor in coauthors:
            if coauthor == main_author:  # Kendi kendine bağlantı kontrolü
                continue

            if coauthor not in author_papers:
                author_papers[coauthor] = []
            author_papers[coauthor].append(paper_title)

            if coauthor not in G:
                G[coauthor] = {}

            # Graf üzerinde kenar ekleme işlemi
            if coauthor in G[main_author]:
                G[main_author][coauthor] += 1  # Var olan kenarın ağırlığını arttırma
            else:
                G[main_author][coauthor] = 1  # Yeni kenar oluşturmak

            if main_author in G[coauthor]:
                G[coauthor][main_author] += 1
            else:
                G[coauthor][main_author] = 1

    # Kendi kendine bağlantıları tamamen silme (kontrol için güvence)
    for author in G:
        if author in G[author]:
            del G[author][author]

    return G, author_papers

def graph_to_json(G, author_papers):
    # Toplam kenar ağırlıklarını ve dereceyi hesaplamak
    total_weights = {}
    degrees = {}

    for node in G:
        total_weight = sum(G[node].values())
        total_weights[node] = total_weight
        degrees[node] = len(G[node])

    # Ortalama kenar ağırlığı ve eşik değerini hesaplamak
    total_sum = sum(total_weights.values())
    average_weight = total_sum / len(total_weights) if total_weights else 0
    threshold = average_weight * 1.2

    # Düğümler JSON
    nodes_data = []
    for node in G:
        total_weight = total_weights.get(node, 0)
        degree = degrees.get(node, 0)
        if total_weight > threshold:
            size = 20 + degree * 2
            color = "darkblue"
        else:
            size = 10 + degree * 1.5
            color = "lightblue"

        papers = author_papers.get(node, [])
        nodes_data.append({
            'id': node,
            'label': node,
            'title': f"Yazar: {node}<br>Makaleler: {', '.join(papers)}",
            'size': size,
            'color': color,
            'paper_count': len(papers),  # Makale sayısı
            'paper_titles': papers          # Makale başlıkları
        })

    # Kenarlar JSON
    edges_data = []
    added_edges = set()
    for u in G:
        for v, weight in G[u].items():
            if (u, v) not in added_edges and (v, u) not in added_edges:
                edges_data.append({
                    'from': u,
                    'to': v,
                    'value': weight
                })
                added_edges.add((u, v))

    return json.dumps({'nodes': nodes_data, 'edges': edges_data})

def dijkstra_shortest_path(graph, source, target):
    distances = {node: sys.maxsize for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0
    unvisited = set(graph.keys())

    while unvisited:
        # En küçük mesafeye sahip düğümü seç
        current = min(
            (node for node in unvisited),
            key=lambda node: distances[node],
            default=None
        )
        if current is None:
            break
        if distances[current] == sys.maxsize:
            break
        if current == target:
            break
        unvisited.remove(current)

        for neighbor, weight in graph[current].items():
            if neighbor in unvisited:
                alt = distances[current] + weight
                if alt < distances[neighbor]:
                    distances[neighbor] = alt
                    previous[neighbor] = current

    # Yol oluşturma
    path = []
    node = target
    if distances[node] < sys.maxsize:
        while node:
            path.insert(0, node)
            node = previous[node]

    return path, distances[target]

def dijkstra_all_shortest_paths(graph, source):
    distances = {node: sys.maxsize for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0
    unvisited = set(graph.keys())

    while unvisited:
        # En küçük mesafeye sahip düğümü seç
        current = min(
            (node for node in unvisited),
            key=lambda node: distances[node],
            default=None
        )
        if current is None:
            break
        if distances[current] == sys.maxsize:
            break
        unvisited.remove(current)

        for neighbor, weight in graph[current].items():
            if neighbor in unvisited:
                alt = distances[current] + weight
                if alt < distances[neighbor]:
                    distances[neighbor] = alt
                    previous[neighbor] = current

    # Yol oluşturma
    paths = {}
    for node in graph:
        path = []
        current = node
        if distances[node] < sys.maxsize:
            while current:
                path.insert(0, current)
                current = previous[current]
        paths[node] = path
    return paths, distances

def find_longest_path(graph, start):
    longest_path = []
    visited = set()

    def dfs(current, path):
        nonlocal longest_path
        visited.add(current)
        path.append(current)

        if len(path) > len(longest_path):
            longest_path = list(path)

        for neighbor in graph[current]:
            if neighbor not in visited:
                dfs(neighbor, path)

        path.pop()
        visited.remove(current)

    dfs(start, [])
    return longest_path

def most_collaborative_author(graph):
    max_collab = -1
    most_collab_author = None
    for author, collaborators in graph.items():
        collab_count = len(collaborators)
        if collab_count > max_collab:
            max_collab = collab_count
            most_collab_author = author
    return most_collab_author, max_collab

@app.route('/', methods=['GET'])
def home_get():
    return render_template('index.html')

@app.route('/process_request', methods=['POST'])
def process_request():
    data = request.get_json()
    action = data.get('action')
    author_a = data.get('author_a', '').strip()
    author_b = data.get('author_b', '').strip()
    try:
        G, author_papers = create_graph(EXCEL_FILE_PATH)

        if action == 'shortest_path':
            if not author_a or not author_b:
                raise ValueError("Her iki yazarın adı girilmelidir!")

            if author_a not in G or author_b not in G:
                raise ValueError("Girilen yazarlar grafikte bulunamadı!")

            # En kısa yol hesaplama
            path, length = dijkstra_shortest_path(G, author_a, author_b)
            if not path:
                raise ValueError(f"{author_a} ile {author_b} arasında bağlantı yok.")
            return jsonify({
                'status': 'success',
                'result': f"En kısa yol: {' → '.join(path)} (Uzunluk: {length})",
                'highlight_nodes': path
            })

        elif action == 'priority_queue':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")

            if author_a not in G:
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            # Yazarın işbirlikçilerini ağırlıklarına göre sıralamak
            collaborators = G[author_a]
            sorted_collaborators = sorted(collaborators.items(), key=lambda x: x[1], reverse=True)

            # Kuyruğa adım adım eklenen elemanları göstermek için
            queue_steps = []
            for collaborator, weight in sorted_collaborators:
                queue_steps.append(f"{collaborator}: {weight}")

            return jsonify({
                'status': 'success',
                'result': f"Queue başarıyla oluşturuldu. Toplam: {len(sorted_collaborators)} kişi.",
                'queue_steps': queue_steps
            })

        elif action == 'create_bst':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")

            if author_a not in G:
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            # Ortak çalışanların sıralı listesini alın
            collaborators = sorted(G[author_a].keys())

            # BST oluşturun (ancak arka uç olduğu için yalnızca sıralanmış listeyi döndürün)
            # Normalde BST yapısı daha fazla ayrıntı gerektirir ancak görsellik için sıralı liste yeterlidir
            return jsonify({
                'status': 'success',
                'result': f"BST Oluşturulan Düğümler: {', '.join(collaborators)}",
                'highlight_nodes': collaborators
            })

        elif action == 'shortest_paths_all':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")

            if author_a not in G:
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            # Dijkstra'nın tüm en kısa yolları
            paths, distances = dijkstra_all_shortest_paths(G, author_a)

            # Sadece `author_a` ile başlayan yolları alın
            filtered_paths = {node: path for node, path in paths.items() if
                              path and path[0] == author_a and node != author_a}

            # Sonuçları metin formatında oluşturun
            result_text = "<br>".join(
                [f"{node}: {' → '.join(path)} (Uzunluk: {distances[node]})" for node, path in filtered_paths.items()]
            )

            # Sadece `author_a` ile bağlantılı düğümleri vurgulayın
            highlight_nodes = set()
            for path in filtered_paths.values():
                highlight_nodes.update(path)
            highlight_nodes = list(highlight_nodes)  # `set`'i `list`'e dönüştürdük

            return jsonify({
                'status': 'success',
                'result': f"<b>{author_a} ile diğer yazarlar arasındaki kısa yollar:</b><br>{result_text}",
                'highlight_nodes': highlight_nodes
            })

        elif action == 'count_collaborators':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")

            if author_a not in G:
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            total = len(G[author_a])
            return jsonify({
                'status': 'success',
                'result': f"{author_a} toplam {total} yazarla işbirliği yapmıştır."
            })

        elif action == 'most_collaborative_author':
            most_col, num_collaborations = most_collaborative_author(G)
            if most_col is None:
                raise ValueError("Grafikte hiç yazar bulunamadı.")
            return jsonify({
                'status': 'success',
                'result': f"En Çok İşbirliği Yapan Yazar: {most_col} ({num_collaborations} işbirliği)",
                'highlight_nodes': [most_col]
            })

        elif action == 'longest_path':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")

            if author_a not in G:
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            # Author_a'dan en uzun yolu bulun
            longest_path = find_longest_path(G, author_a)
            if not longest_path:
                raise ValueError(f"{author_a} ile herhangi bir yazar arasında yol bulunamadı.")
            return jsonify({
                'status': 'success',
                'result': f"En Uzun Yol: {' → '.join(longest_path)}",
                'highlight_nodes': longest_path
            })

        return jsonify({'status': 'error', 'result': 'Geçersiz işlem!'})

    except Exception as e:
        return jsonify({'status': 'error', 'result': str(e)})

@app.route('/get_graph_data', methods=['GET'])
def get_graph_data():
    try:
        G, author_papers = create_graph(EXCEL_FILE_PATH)
        graph_json = graph_to_json(G, author_papers)
        return jsonify(json.loads(graph_json))
    except Exception as e:
        return jsonify({"error": f"Grafik verisi yüklenirken hata oluştu: {e}"})

if __name__ == '__main__':
    app.run(debug=True)
