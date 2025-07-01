#include <iostream>
using namespace std;


int main(){

    int n;
    cin >>n;


    for(int i=0; i<n; i++){

        for(int space=0; space<i; space++ ){
            cout << " ";
        }

        for(int j=n-i; j >= 1; j--){
            cout << i+1;
        };
        cout << endl;

    }

    return 0;
};