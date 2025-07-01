#include <iostream>
using namespace std;


int main(){
    int n;
    cin >> n;

    for(int i=0; i < n; i++){
        char ch;
        for(int j=i; j>=0; j--){
            ch = 'A' + j;
            cout << ch<< " ";
        }
        cout << endl;
    }
    return 0;
}