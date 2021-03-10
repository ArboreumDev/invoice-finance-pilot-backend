import { VStack } from "@chakra-ui/react";
import useSWR from "swr";
import axios from "axios";
import LenderDashboard from "./LenderDashboard";
import BorrowerDashboard from "./BorrowerDashboard";
import AdminDashboard from "./AdminDashboard";
// import React from "react";
import { useRouter } from "next/router";
import React, { useEffect } from "react";

// for rc-admin role
const SUPER_AUTH_TOKEN = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJyYyIsImV4cCI6MjA0Njk2MzQ1Niwicm9sZSI6InJjX2FkbWluIn0.GV0Q2mPmMUT4In6ro8QL_LO-nsXqUIV6NUlg46Q2_eg"


export const axiosInstance = axios.create({
  baseURL: "http://localhost:8000/",
  headers: { Authorization: SUPER_AUTH_TOKEN },
});

export enum ShipmentStatus {
  DEFAULTED = "DEFAULTED",
  AWAITING_SHIPMENT = "AWAITING_SHIPMENT",
  SHIPPING = "SHIPPING",
  DELIVERED = "DELIVERED",
}

export enum FinanceStatus {
  NONE = "NONE",
  FINANCED = "FINANCED",
  REPAID = "REPAID",
  DEFAULTED = "DEFAULTED",
}

export interface Invoice {
  id: number;
  amount: number;
  destination: string;
  shippingStatus: ShipmentStatus;
  status: FinanceStatus;
  // endDate: Date
}

// TODO: Fetch loans from API but use the following for dev
const invoice_fixtures: Invoice[] = [
  {
    id: 1,
    amount: 1000,
    destination: "Ramesh",
    status: FinanceStatus.NONE,
    shippingStatus: ShipmentStatus.AWAITING_SHIPMENT,
  },
  {
    id: 2,
    amount: 1000,
    destination: "Ajit",
    status: FinanceStatus.NONE,
    shippingStatus: ShipmentStatus.AWAITING_SHIPMENT,
  },
  {
    id: 3,
    amount: 1000,
    destination: "Pavan",
    status: FinanceStatus.NONE,
    shippingStatus: ShipmentStatus.AWAITING_SHIPMENT,
  },
];

export const fetcher = (url) => axiosInstance.get(url).then((res) => res.data);

const getInvoices = () => {
  const router = useRouter();
  useEffect(function mount() {
    console.log('washere')
    const r = JSON.parse(window.localStorage.getItem("arboreum:info"))
    if (!r) {
      console.log("couldnt find user info!")
      router.push("/login");
    } else {
      console.log("found user info. set token to the one from storage", r)
      axiosInstance.defaults.headers.common["Auth-Token"] = r.token
      console.log(axiosInstance.defaults.headers)
    }
  })  
  const { data, error } = useSWR<Invoice[]>("/v1/invoice", fetcher, {
    refreshInterval: 10000,
  });
  return {
    invoices: data,
    isLoading: !error && !data,
    isError: error,
  };
};

const Main = () => {
  const { invoices, isLoading, isError } = getInvoices();
  return (
    <VStack align="left" textAlign="left" p="20px">
      <LenderDashboard
        invoices={invoices}
        isLoading={isLoading}
        isError={isError}
      />
      {/* <AdminDashboard
        invoices={invoices}
        isLoading={isLoading}
        isError={isError}
      />
      <BorrowerDashboard /> */}
    </VStack>
  );
};

export default Main;
