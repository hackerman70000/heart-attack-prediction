import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, accuracy_score, mean_squared_error
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.svm import SVC
from tabulate import tabulate

from data_fetch import fetch_data


def process_target(df):
    df['target'] = df['num'].apply(lambda x: 1 if x > 0 else 0)
    df.drop('num', axis=1, inplace=True)
    return df


def results(y_test, y_pred):
    precision = precision_score(y_test, y_pred, zero_division=1)
    recall = recall_score(y_test, y_pred, zero_division=1)
    accuracy = accuracy_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    print_results(precision, recall, accuracy, mse)


def print_results(precision, recall, accuracy, mse):
    table = [
        ["Precision", round(precision, 3)],
        ["Recall", round(recall, 3)],
        ["Accuracy", round(accuracy, 3)],
        ["Mean Squared Error", round(mse, 3)]
    ]
    print(tabulate(table, headers=["Metric", "Value"], tablefmt="grid"))


def evaluate_model(pipeline, X_train, X_test, y_train, y_test):
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    results(y_test, y_pred)
    return accuracy_score(y_test, y_pred)


def handle_outliers(df):
    for col in ['age', 'trestbps', 'chol', 'thalach', 'oldpeak']:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        df[col] = np.where(df[col] < lower_bound, lower_bound, df[col])
        df[col] = np.where(df[col] > upper_bound, upper_bound, df[col])
    return df


def XGBoost_pipeline(X_train, X_test, y_train, y_test):
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', RobustScaler()),
        ('clf', xgb.XGBClassifier(
            learning_rate=0.1,
            max_depth=1,
            n_estimators=50,
            colsample_bytree=0.5
        ))
    ])

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')

    print('\n', 'Results for XGBoost pipeline:')
    print("Mean CV accuracy:", round(np.mean(cv_scores), 3))
    return evaluate_model(pipeline, X_train, X_test, y_train, y_test)


def SVM_pipeline(X_train, X_test, y_train, y_test):
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', RobustScaler()),
        ('clf', SVC())
    ])

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')

    print('\n', 'Results for SVM pipeline:')
    print("Mean CV accuracy:", round(np.mean(cv_scores), 3))
    return evaluate_model(pipeline, X_train, X_test, y_train, y_test)


def LR_pipeline(X_train, X_test, y_train, y_test):
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression())
    ])

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')

    print('\n', 'Results for Logistic Regression pipeline:')
    print("Mean CV accuracy:", round(np.mean(cv_scores), 3))
    return evaluate_model(pipeline, X_train, X_test, y_train, y_test)


def KN_pipeline(X_train, X_test, y_train, y_test):
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('clf', KNeighborsClassifier())
    ])

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')

    print('\n', 'Results for KNeighbors pipeline:')
    print("Mean CV accuracy:", round(np.mean(cv_scores), 3))
    return evaluate_model(pipeline, X_train, X_test, y_train, y_test)


def evaluate_models_iteratively(X, y, num):
    accuracies = {'KNeighbors': [], 'Logistic Regression': [], 'SVM': [], 'XGBoost': []}

    for i in range(num):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        KN_acc = KN_pipeline(X_train, X_test, y_train, y_test)
        LR_acc = LR_pipeline(X_train, X_test, y_train, y_test)
        SVM_acc = SVM_pipeline(X_train, X_test, y_train, y_test)
        XGB_acc = XGBoost_pipeline(X_train, X_test, y_train, y_test)

        accuracies['KNeighbors'].append(KN_acc)
        accuracies['Logistic Regression'].append(LR_acc)
        accuracies['SVM'].append(SVM_acc)
        accuracies['XGBoost'].append(XGB_acc)

    mean_accuracies = {model: np.mean(acc_list) for model, acc_list in accuracies.items()}

    plot_performance(accuracies, mean_accuracies)


def evaluate_models_once(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    KN_pipeline(X_train, X_test, y_train, y_test)
    LR_pipeline(X_train, X_test, y_train, y_test)
    SVM_pipeline(X_train, X_test, y_train, y_test)
    XGBoost_pipeline(X_train, X_test, y_train, y_test)


def plot_performance(accuracies, mean_accuracies):
    plt.figure(figsize=(10, 6))
    for model, acc_list in accuracies.items():
        acc_list_sorted = sorted(acc_list)
        plt.plot([acc_list_sorted[0], acc_list_sorted[-1]], [model, model], 'b-')
        plt.plot([mean_accuracies[model]], [model], 'bo')
        plt.plot([acc_list_sorted[0]], [model], 'b|', markersize=10)
        plt.plot([acc_list_sorted[-1]], [model], 'b|', markersize=10)

    plt.title('Accuracy of Different Models')
    plt.xlabel('Accuracy')
    plt.ylabel('Model')
    plt.yticks(range(len(accuracies)), list(accuracies.keys()))
    plt.grid(axis='y')
    plt.show()


def main():
    try:
        df = pd.read_csv('heart_disease.csv')
    except FileNotFoundError:
        fetch_data()
        try:
            df = pd.read_csv('heart_disease.csv')
        except FileNotFoundError:
            print('Error fetching data. Please try again.')
            exit(1)

    df = df.dropna().reset_index(drop=True)
    df = process_target(df)
    df = handle_outliers(df)

    X = df[['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca',
            'thal']]
    y = df['target']

    # Example usage: models evaluated iteratively with 100 iterations
    evaluate_models_iteratively(X, y, 100)

    # Example usage: single model evaluation
    evaluate_models_once(X, y)


if __name__ == "__main__":
    main()
