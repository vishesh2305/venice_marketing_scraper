// Decimal to binary 
#include <iostream>
using namespace std;


long int binary(long long int a ){
    int ans =0;
    int pow = 1;
    while(a > 0){
        int remainder = a % 2;
        a = a/2;
        ans +=  remainder*pow;
        pow *=10;
    }

    return ans;
};


int main(){
    long int a = 1111;

    cout << binary(a);

    return 0;
}