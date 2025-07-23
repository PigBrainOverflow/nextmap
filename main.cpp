#include <memory>
#include <set>
#include <map>
#include <string>
#include <iostream>

template <typename T, typename U>
class Trie {
public:
    using TConstIterType = typename T::const_iterator;

    struct TrieNode {
        TrieNode() = default;
        std::map<typename T::value_type, std::unique_ptr<TrieNode>> children;
        std::set<U> values;
    };

    Trie() : root(std::make_unique<TrieNode>()) {}
    ~Trie() = default;

    void insert(const T& key, U value) {
        auto cur = root.get();
        for (const auto& cur_key : key) {
            auto& next = cur->children[cur_key];
            if (!next) {
                next = std::make_unique<TrieNode>();
            }
            cur = next.get();
        }
        cur->values.insert(std::move(value));
    }

    const std::set<U>* find(const T& key) {
        // returns nullptr if not found
        auto cur = root.get();
        for (const auto& cur_key : key) {
            auto itr = cur->children.find(cur_key);
            if (itr == cur->children.end()) {   // not found
                return nullptr;
            }
            cur = itr->second.get();
        }
        return &cur->values;
    }

    std::set<U> subseq_of(const T& key) {
        // find all values whose keys are subsets of the given key
        std::set<U> res;
        subseq_of_recursive(res, root.get(), key.cbegin(), key.cend());
        return res;
    }

private:
    std::unique_ptr<TrieNode> root;

    void subseq_of_recursive(std::set<U>& res, const TrieNode* node, TConstIterType key_itr, const TConstIterType& key_end) {
        if (node) {
            res.insert(node->values.begin(), node->values.end());
            while (key_itr != key_end) {
                auto itr = node->children.find(*key_itr);
                if (itr == node->children.end()) {
                    break;  // no further children match
                }
                ++key_itr;
                subseq_of_recursive(res, itr->second.get(), key_itr, key_end);
            }
        }
    }
};

int main() {
    Trie<std::string, int> trie;
    trie.insert(std::string("hello"), 1);
    trie.insert(std::string("hell"), 2);
    trie.insert(std::string("helloworld"), 3);
    auto res = trie.subseq_of(std::string("hello"));
    for (const auto& val : res) {   // expected output: 1 2
        std::cout << val << " ";
    }
    std::cout << std::endl;
    res = trie.subseq_of(std::string("helloworld"));
    for (const auto& val : res) {   // expected output: 1 2 3
        std::cout << val << " ";
    }
    std::cout << std::endl;
    return 0;
}