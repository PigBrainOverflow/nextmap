#ifndef TRIE_H
#define TRIE_H

// #include <memory>
#include <pybind11/stl.h>


namespace emapcc {

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

    void insert(const T& key, U value);
    const std::set<U>* find(const T& key) const;
    std::set<U> subseq_of(const T& key) const;
    void remove(const T& key, U value);

private:
    std::unique_ptr<TrieNode> root;

    void subseq_of_recursive(std::set<U>& res, const TrieNode* node, TConstIterType key_itr, const TConstIterType& key_end) const;
};

template <typename T, typename U>
void Trie<T, U>::insert(const T& key, U value) {
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

template <typename T, typename U>
const std::set<U>* Trie<T, U>::find(const T& key) const {
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

template <typename T, typename U>
std::set<U> Trie<T, U>::subseq_of(const T& key) const {
    // find all values whose keys are subsets of the given key
    std::set<U> res;
    subseq_of_recursive(res, root.get(), key.cbegin(), key.cend());
    return res;
}

template <typename T, typename U>
void Trie<T, U>::subseq_of_recursive(std::set<U>& res, const TrieNode* node, TConstIterType key_itr, const TConstIterType& key_end) const {
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

template <typename T, typename U>
void Trie<T, U>::remove(const T& key, U value) {
    // TODO: also remove the node if it becomes empty
    auto cur = root.get();
    for (const auto& cur_key : key) {
        auto itr = cur->children.find(cur_key);
        if (itr == cur->children.end()) {
            return;  // key not found, nothing to remove
        }
        cur = itr->second.get();
    }
    cur->values.erase(value);  // remove the value
}

}

#endif