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
        df = df.iloc[:250]
    except Exception as e:
        raise ValueError(f"Excel dosyası okunamadı: {e}")

    G = {}
    author_papers = {}

    for _, row in df.iterrows():
        main_author = row['author_name']
        coauthors = [coauthor.strip() for coauthor in row['coauthors'].split(",") if coauthor.strip()]
        paper_title = row['paper_title']

        if main_author not in author_papers:
            author_papers[main_author] = []
        author_papers[main_author].append(paper_title)

        if main_author not in G:
            G[main_author] = {}

        for co_author in coauthors:
            if co_author not in G:
                G[co_author] = {}
            if co_author != main_author:
                if co_author in G[main_author]:
                    G[main_author][co_author] += 1
                else:
                    G[main_author][co_author] = 1

                if main_author in G[co_author]:
                    G[co_author][main_author] += 1
                else:
                    G[co_author][main_author] = 1

    return G, author_papers

def graph_to_json(G, author_papers):
    graph = nx.Graph()
    for node, edges in G.items():
        for neighbor, weight in edges.items():
            graph.add_edge(node, neighbor, weight=weight)

        # Toplam kenar ağırlıklarını hesapla
    total_weights = {}
    degrees = {}
    for node in graph.nodes():
        total_weight = sum(data['weight'] for _, _, data in graph.edges(node, data=True))
        total_weights[node] = total_weight
        degrees[node] = graph.degree(node)  # Düğüm bağlantı sayısı

        # Ortalama kenar ağırlığını hesapla
    total_sum = sum(total_weights.values())
    average_weight = total_sum / len(total_weights) if total_weights else 0
    threshold = average_weight * 1.2  # %20 üzerinde olanlar için threshold

    # Düğümleri JSON formatına ekle
    nodes_data = []
    for node in graph.nodes():
        total_weight = total_weights.get(node, 0)
        degree = degrees.get(node, 0)
        if total_weight > threshold:
            size = 20 + degree * 2  # Büyük düğümler için ekstra boyut (bağlantı sayısına göre artar)
            color = "darkblue"  # Koyu renk
        else:
            size = 10 + degree * 1.5  # Küçük düğümler için boyut
            color = "lightblue"  # Açık renk

        nodes_data.append({
            'id': node,
            'label': node,
            'title': f"Yazar: {node}<br>Makaleler: {', '.join(author_papers.get(node, []))}",
            'size': size,
            'color': color
        })

    # Kenarları JSON formatına ekle
    edges_data = []
    for u, v, data in graph.edges(data=True):
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
            path = nx.single_source_dijkstra_path(G, start)
            length = nx.single_source_dijkstra_path_length(G, start)
            return path, length
    except Exception as e:
        raise ValueError(f"Dijkstra algoritması uygulanamadı: {e}")

def most_collaborative_author(G):
    most_collaborative = None
    max_collaborations = 0

    for author, collaborators in G.items():
        num_collaborations = len(collaborators)
        if num_collaborations > max_collaborations:
            most_collaborative = author
            max_collaborations = num_collaborations

    return most_collaborative, max_collaborations

def find_longest_path(G, start):
    visited = set()
    longest_path = []

    def dfs(node, path):
        nonlocal longest_path
        visited.add(node)
        path.append(node)

        if len(path) > len(longest_path):
            longest_path = list(path)

        for neighbor in G.get(node, {}):
            if neighbor not in visited:
                dfs(neighbor, path)

        path.pop()
        visited.remove(node)

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
    most_collaborative = None
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
            author_a = request.form.get('author_a')
            author_b = request.form.get('author_b')

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
            author_a = request.form.get('author_a')

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            collaborators = G.get(author_a, {})
            queue = sorted(collaborators.items(), key=lambda x: x[1], reverse=True)

        elif action == 'create_bst':
            author_a = request.form.get('author_a')
            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            collaborators = G.get(author_a, {})
            queue = sorted(collaborators.items(), key=lambda x: x[1], reverse=True)
            bst_root = None

            # Basit bir ikili arama ağacı (BST) sınıfı
            class BSTNode:
                def __init__(self, key):
                    self.left = None
                    self.right = None
                    self.value = key

            # BST'ye yazar ekleme fonksiyonu
            def insert_bst(root, key):
                if root is None:
                    return BSTNode(key)
                else:
                    if key < root.value:
                        root.left = insert_bst(root.left, key)
                    else:
                        root.right = insert_bst(root.right, key)
                return root

            # BST'den yazar çıkarma fonksiyonu
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

            # BST'de minimum değeri bulma fonksiyonu
            def find_min(root):
                current = root
                while current.left is not None:
                    current = current.left
                return current

            # BST oluşturma
            for author, _ in queue:
                bst_root = insert_bst(bst_root, author)

            # Kullanıcıdan çıkarılacak yazarı al
            remove_author = request.form.get('remove_author')
            if remove_author:
                bst_root = remove_bst(bst_root, remove_author)

            # BST'yi liste olarak almak için in-order traversal
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
            author_a = request.form.get('author_a')

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            try:
                paths, lengths = dijkstra_algorithm(G, author_a)
                graph_json = graph_to_json(G, author_papers)
            except ValueError as ve:
                error = str(ve)
                return render_template('index.html', error=error)

        elif action == 'count_collaborators':
            author_a = request.form.get('author_a')

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            total_collaborations = len(G.get(author_a, {}))

        elif action == 'most_collaborative':
            most_collaborative, num_collaborations = most_collaborative_author(G)

        elif action == 'longest_path':
            author_a = request.form.get('author_a')

            if not author_a:
                error = "Lütfen yazar adını girin."
                return render_template('index.html', error=error)

            longest_path = find_longest_path(G, author_a)

        # Grafik verisini JSON formatına dönüştürme
        if action in ['shortest_path', 'shortest_paths_all', 'priority_queue', 'create_bst']:
            graph_json = graph_to_json(G, author_papers)

        return render_template('index.html',
                               graph_data=graph_json,
                               path=path,
                               length=length,
                               most_collaborative=most_collaborative,
                               num_collaborations=num_collaborations,
                               author_a=author_a,
                               author_b=author_b,
                               queue=queue,
                               bst=bst,
                               longest_path=longest_path,
                               total_collaborations=total_collaborations,
                               paths=paths,
                               error=error)

    return render_template('index.html') # GET isteği için render_template çağrısı

@app.route('/process_request', methods=['POST'])
def process_request():
    data = request.get_json()
    action = request.json.get('action')

    try:
        G, author_papers = create_graph(EXCEL_FILE_PATH)

        if action == 'most_collaborative_author':
            most_collaborative, num_collaborations = most_collaborative_author(G)
            return jsonify({
                'status': 'success',
                'result': f"En Çok İşbirliği Yapan Yazar: {most_collaborative} ({num_collaborations} işbirliği)"
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
#@app.route('/')
#def index():
 #   return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
