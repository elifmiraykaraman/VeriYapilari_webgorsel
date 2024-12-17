from flask import Flask, render_template, request, jsonify
import pandas as pd
import networkx as nx
import json
import os

app = Flask(__name__)

# Excel dosyasının yolu
EXCEL_FILE_PATH = r"C:\Users\Acer\PycharmProjects\PROLAB_3\PROLAB 3 - GUNCEL DATASET.xlsx"

def create_graph(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.iloc[:500]  # Gerekirse ilk 500 satırı kullanın
    except Exception as e:
        raise ValueError(f"Excel dosyası okunamadı: {e}")

    G = nx.Graph()
    author_papers = {}

    for _, row in df.iterrows():
        # Yazar isimlerini temizle
        main_author = str(row['author_name']).strip().strip("'").strip('"').strip('[]')
        coauthors = [
            coauthor.strip().strip("'").strip('"').strip('[]')
            for coauthor in str(row['coauthors']).split(",")
            if coauthor.strip()
        ]

        paper_title = str(row['paper_title']).strip()

        # Ana yazarın makale listesini güncelle
        if main_author not in author_papers:
            author_papers[main_author] = []
        author_papers[main_author].append(paper_title)

        # Ana yazar düğümü ekle
        if not G.has_node(main_author):
            G.add_node(main_author)

        # Ortak yazarları ekle
        for co_author in coauthors:
            if co_author not in author_papers:
                author_papers[co_author] = []
            author_papers[co_author].append(paper_title)

            if not G.has_node(co_author):
                G.add_node(co_author)

            # Kenar mevcutsa ağırlığı arttır, yoksa yeni ekle
            if G.has_edge(main_author, co_author):
                G[main_author][co_author]['weight'] += 1
            else:
                G.add_edge(main_author, co_author, weight=1)

    return G, author_papers

def graph_to_json(G, author_papers):
    # Toplam kenar ağırlıklarını hesapla
    total_weights = {}
    degrees = {}

    for node in G.nodes():
        total_weight = sum(data['weight'] for _, _, data in G.edges(node, data=True))
        total_weights[node] = total_weight
        degrees[node] = G.degree(node)

    # Ortalama kenar ağırlığı
    total_sum = sum(total_weights.values())
    average_weight = total_sum / len(total_weights) if total_weights else 0
    threshold = average_weight * 1.2

    # Düğümler JSON
    nodes_data = []
    for node in G.nodes():
        total_weight = total_weights.get(node, 0)
        degree = degrees.get(node, 0)
        if total_weight > threshold:
            size = 20 + degree * 2
            color = "darkblue"
        else:
            size = 10 + degree * 1.5
            color = "lightblue"

        nodes_data.append({
            'id': node,
            'label': node,
            'title': f"Yazar: {node}<br>Makaleler: {', '.join(author_papers.get(node, []))}",
            'size': size,
            'color': color
        })

    # Kenarlar JSON
    edges_data = []
    for u, v, data in G.edges(data=True):
        edges_data.append({
            'from': u,
            'to': v,
            'value': data['weight']
        })

    return json.dumps({'nodes': nodes_data, 'edges': edges_data})

def dijkstra_algorithm(G, start, end=None):
    try:
        if end:
            path = nx.shortest_path(G, source=start, target=end, weight='weight')
            length = nx.shortest_path_length(G, source=start, target=end, weight='weight')
            return path, length
        else:
            # Tüm düğümlere olan en kısa yollar
            paths = nx.single_source_dijkstra_path(G, start, weight='weight')
            lengths = nx.single_source_dijkstra_path_length(G, start, weight='weight')
            return paths, lengths
    except nx.NetworkXNoPath:
        raise ValueError(f"Dijkstra algoritması uygulanamadı: '{start}' ve '{end}' arasında yol yok.")
    except Exception as e:
        raise ValueError(f"Dijkstra algoritması uygulanamadı: {e}")

def most_collaborative_author(G):
    most_collaborative = None
    max_collaborations = 0

    for author in G.nodes():
        num_collaborations = G.degree(author)
        if num_collaborations > max_collaborations:
            most_collaborative = author
            max_collaborations = num_collaborations

    return most_collaborative, max_collaborations

def find_longest_path(G, start):
    # Bu DFS ile en uzun yolu bulma fonksiyonu, bağlı bir bileşende en uzun basit yolu bulmaya çalışır.
    # Not: En uzun yol problemi NP-zordur, burada basit bir DFS yaklaşımı var,
    # Tüm yollara bakar (küçük veri setlerinde çalışabilir ancak büyük setlerde yavaş olabilir).
    visited = set()
    longest_path = []

    def dfs(node, path):
        nonlocal longest_path
        visited.add(node)
        path.append(node)

        if len(path) > len(longest_path):
            longest_path = list(path)

        for neighbor in G[node]:
            if neighbor not in visited:
                dfs(neighbor, path)

        path.pop()
        visited.remove(node)

    if G.has_node(start):
        dfs(start, [])
    return longest_path

def calculate_author_statistics(df):
    author_article_count = df['author_name'].value_counts().to_dict()
    average = sum(author_article_count.values()) / len(author_article_count)
    threshold = average * 1.2
    return author_article_count, threshold

@app.route('/', methods=['GET', 'POST'])
def home():
    graph_json = None
    path = None
    length = None
    most_col = None
    num_collaborations = None
    author_a = None
    author_b = None
    error = None
    queue = None
    bst = None
    longest_path = None
    total_collaborations = None
    paths = None

    try:
        # Grafiği oluştur
        G, author_papers = create_graph(EXCEL_FILE_PATH)
        df = pd.read_excel(EXCEL_FILE_PATH)
        author_article_count, threshold = calculate_author_statistics(df)
    except Exception as e:
        error = f"Veri seti yüklenirken hata oluştu: {e}"
        return render_template('index.html', error=error)

    if request.method == 'POST':
        action = request.form.get('action')

        try:
            G, author_papers = create_graph(EXCEL_FILE_PATH)
            df = pd.read_excel(EXCEL_FILE_PATH)
            author_article_count, threshold = calculate_author_statistics(df)
        except ValueError as ve:
            error = str(ve)
            return render_template('index.html', error=error)

        if action == 'shortest_path':
            author_a = request.form.get('author_a', '').strip()
            author_b = request.form.get('author_b', '').strip()

            if not author_a or not author_b:
                error = "Lütfen her iki yazar adını da girin."
                return render_template('index.html', error=error)

            try:
                path, length = dijkstra_algorithm(G, author_a, author_b)
                graph_json = graph_to_json(G, author_papers)
            except ValueError as ve:
                error = str(ve)
                return render_template('index.html', error=error)

        elif action == 'priority_queue':
            author_a = request.form.get('author_a', '').strip()

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            if not G.has_node(author_a):
                error = f"{author_a} graf içerisinde bulunamadı."
                return render_template('index.html', error=error)

            # Priority Queue: komşuları ağırlıklarına göre sırala
            collaborators = G[author_a]
            queue = sorted(collaborators.items(), key=lambda x: x[1]['weight'], reverse=True)

        elif action == 'create_bst':
            author_a = request.form.get('author_a', '').strip()
            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            if not G.has_node(author_a):
                error = f"{author_a} graf içerisinde bulunamadı."
                return render_template('index.html', error=error)

            # BST oluşturmak için düğümleri sırala
            collaborators = G[author_a]
            sorted_authors = sorted(collaborators.keys())

            class BSTNode:
                def __init__(self, key):
                    self.left = None
                    self.right = None
                    self.value = key

            def insert_bst(root, key):
                if root is None:
                    return BSTNode(key)
                else:
                    if key < root.value:
                        root.left = insert_bst(root.left, key)
                    else:
                        root.right = insert_bst(root.right, key)
                return root

            def find_min(root):
                current = root
                while current.left is not None:
                    current = current.left
                return current

            def remove_bst(root, key):
                if root is None:
                    return root
                if key < root.value:
                    root.left = remove_bst(root.left, key)
                elif key > root.value:
                    root.right = remove_bst(root.right, key)
                else:
                    if root.left is None:
                        temp = root.right
                        root = None
                        return temp
                    elif root.right is None:
                        temp = root.left
                        root = None
                        return temp
                    temp = find_min(root.right)
                    root.value = temp.value
                    root.right = remove_bst(root.right, temp.value)
                return root

            bst_root = None
            for author in sorted_authors:
                bst_root = insert_bst(bst_root, author)

            remove_author = request.form.get('remove_author', '').strip()
            if remove_author:
                bst_root = remove_bst(bst_root, remove_author)

            def inorder_traversal(root, result=None):
                if result is None:
                    result = []
                if root:
                    inorder_traversal(root.left, result)
                    result.append(root.value)
                    inorder_traversal(root.right, result)
                return result

            bst = inorder_traversal(bst_root)

        elif action == 'shortest_paths_all':
            author_a = request.form.get('author_a', '').strip()

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            if not G.has_node(author_a):
                error = f"{author_a} graf içerisinde bulunamadı."
                return render_template('index.html', error=error)

            try:
                paths, lengths = dijkstra_algorithm(G, author_a)
                graph_json = graph_to_json(G, author_papers)
            except ValueError as ve:
                error = str(ve)
                return render_template('index.html', error=error)

        elif action == 'count_collaborators':
            author_a = request.form.get('author_a', '').strip()

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            if not G.has_node(author_a):
                error = f"{author_a} graf içerisinde bulunamadı."
                return render_template('index.html', error=error)

            total_collaborations = G.degree(author_a)

        elif action == 'most_collaborative':
            most_col, num_collaborations = most_collaborative_author(G)

        elif action == 'longest_path':
            author_a = request.form.get('author_a', '').strip()

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            if not G.has_node(author_a):
                error = f"{author_a} graf içerisinde bulunamadı."
                return render_template('index.html', error=error)

            longest_path = find_longest_path(G, author_a)

        # Grafik verisini JSON formatına dönüştür
        if action in ['shortest_path', 'shortest_paths_all', 'priority_queue', 'create_bst']:
            graph_json = graph_to_json(G, author_papers)

        return render_template('index.html',
                               graph_data=graph_json,
                               path=path,
                               length=length,
                               most_collaborative=most_col,
                               num_collaborations=num_collaborations,
                               author_a=author_a,
                               author_b=author_b,
                               queue=queue,
                               bst=bst,
                               longest_path=longest_path,
                               total_collaborations=total_collaborations,
                               paths=paths,
                               error=error)

    return render_template('index.html')  # GET isteği için

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
            path, length = dijkstra_algorithm(G, author_a, author_b)
            return jsonify({
                'status': 'success',
                'result': f"En kısa yol: {' → '.join(path)} (Uzunluk: {length})",
                'highlight_nodes': path
            })

        elif action == 'priority_queue':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")
            if not G.has_node(author_a):
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")
            collaborators = G[author_a]
            sorted_queue = sorted(collaborators.items(), key=lambda x: x[1]['weight'], reverse=True)
            queue_nodes = [author_a] + [node for node, _ in sorted_queue]
            queue_text = "\n".join([f"{co_author}: {data['weight']}" for co_author, data in sorted_queue])
            return jsonify({
                'status': 'success',
                'result': f"Priority Queue:\n{queue_text}",
                'highlight_nodes': queue_nodes
            })

        elif action == 'create_bst':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")
            if not G.has_node(author_a):
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")

            collaborators = G[author_a]
            bst_nodes = sorted(collaborators.keys())
            return jsonify({
                'status': 'success',
                'result': f"BST Oluşturulan Düğümler: {', '.join(bst_nodes)}",
                'highlight_nodes': bst_nodes
            })

        elif action == 'shortest_paths_all':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")
            if not G.has_node(author_a):
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")
            paths, lengths = dijkstra_algorithm(G, author_a)
            result_text = "<br>".join([f"{k}: {' → '.join(v)}" for k, v in paths.items()])
            highlight_nodes = [author_a] + list(paths.keys())
            return jsonify({
                'status': 'success',
                'result': f"<b>Tüm Kısa Yollar:</b><br>{result_text}",
                'highlight_nodes': highlight_nodes
            })

        elif action == 'count_collaborators':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")
            if not G.has_node(author_a):
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")
            total = G.degree(author_a)
            return jsonify({'status': 'success', 'result': f"{author_a} toplam {total} yazarla işbirliği yapmıştır."})

        elif action == 'most_collaborative_author':
            most_col, num_collaborations = most_collaborative_author(G)
            return jsonify({'status': 'success',
                            'result': f"En Çok İşbirliği Yapan Yazar: {most_col} ({num_collaborations} işbirliği)"})

        elif action == 'longest_path':
            if not author_a:
                raise ValueError("Yazar adı girilmelidir!")
            if not G.has_node(author_a):
                raise ValueError(f"{author_a} graf içerisinde bulunamadı.")
            longest_path = find_longest_path(G, author_a)
            return jsonify({
                'status': 'success',
                'result': f"En Uzun Yol: {' → '.join(longest_path)}",
                'highlight_nodes': longest_path
            })

        return jsonify({'status': 'error', 'result': 'Geçersiz işlem!'})

    except Exception as e:
        return jsonify({'status': 'error', 'result': str(e)})

@app.route('/get', methods=['GET'])
def home_get():
    return render_template('index.html')

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
